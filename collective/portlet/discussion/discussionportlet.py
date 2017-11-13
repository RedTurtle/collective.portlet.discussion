from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.portlet.discussion import DiscussionPortletMessageFactory as _
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider
from urllib import urlencode
from zope import schema
from zope.interface import implements
from collective.portlet.discussion.utility.interfaces import\
    ICommentsListUtility
from zope.component import getUtility
from zope.component.interfaces import ComponentLookupError
from plone.app.vocabularies.catalog import CatalogSource
from plone.outputfilters.browser.resolveuid import uuidToObject


class IDiscussionPortlet(IPortletDataProvider):
    """A portlet

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """
    portletTitle = schema.TextLine(
        title=_(u"Portlet title"),
        description=_(u"Insert the portlet title."),
        required=True)

    discussionState = schema.List(
        title=_(u'Discussions state'),
        description=_(u'Select the review state of the discussions. Leave empty'
                      ' to show all the discussions.'),
        value_type=schema.Choice(
            vocabulary="collective.portlet.discussion.DiscussionStatesVocab",
            required=False
        )
    )

    discussionFolder = schema.Choice(
        title=_(u"Discussions folder"),
        description=_(u"Insert the folder where you want to search the"
                      " discussions. Leave empty to search in all the portal."),
        required=False,
        source=CatalogSource(portal_type=('Folder')),
    )

    nDiscussions = schema.Int(
        title=_(u"Number of discussions"),
        required=False,
        default=5,
        description=_(u"Specify how many discussions will be shown in the"
                      " portlet.")
    )


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(IDiscussionPortlet)

    def __init__(self,
                 portletTitle='',
                 nDiscussions=5,
                 discussionFolder=None,
                 discussionState=''):
        self.portletTitle = portletTitle
        self.nDiscussions = nDiscussions
        self.discussionFolder = discussionFolder
        self.discussionState = discussionState

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        if self.data.portletTitle:
            return self.data.portletTitle
        else:
            return "Discussions portlet"


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ViewPageTemplateFile('discussionportlet.pt')

    @property
    def available(self):
        try:
            if self.getDiscussionsList():
                return True
            else:
                return False
        except AttributeError:
            return False

    def getPortletTitle(self):
        """return the portlet title"""
        if self.data.portletTitle:
            return self.data.portletTitle
        else:
            return _("Discussions")

    def getDiscussionsList(self):
        """return a list of discussions"""
        try:
            utility = getUtility(ICommentsListUtility,
                                 name="comments_list_utility")(self.context)
            return utility(self.setQuery())
        except ComponentLookupError:
            return []

    def setQuery(self):
        """set the query for discussion search"""
        query = {'portal_type': 'Discussion Item',
                 'sort_on': 'created',
                 'sort_order': 'reverse'}

        if self.data.discussionFolder:
            query['path'] = '/'.join(
                uuidToObject(self.data.discussionFolder).getPhysicalPath()
            )

        if len(self.data.discussionState) == 1:
            query['review_state'] = self.data.discussionState[0]
        return query

    def urlencodeQuery(self):
        """return the query urlencoded"""
        return urlencode(self.setQuery())


class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    schema = IDiscussionPortlet
    label = _(u"Add Discussion Portlet")
    description = _(u"This portlet displays a list of comments.")

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    schema = IDiscussionPortlet
    label = _(u"Edit Discussion Portlet")
    description = _(u"This portlet displays a list of comments.")
