from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from seuranta.models import Competition, Competitor, RouteSection, Map


class PublisherAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if obj.publisher_id is None:
            obj.publisher = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(PublisherAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(publisher=request.user)

    def has_add_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        else:
            return obj.publisher == request.user

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        else:
            return obj.publisher == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if obj is None:
            return True
        else:
            return obj.publisher == request.user


class RouteSectionInlineAdmin(admin.TabularInline):
    model = RouteSection


class CompetitorInlineAdmin(admin.StackedInline):
    model = Competitor
    prepopulated_fields = {'short_name': ('name',), }


class MapInlineAdmin(admin.TabularInline):
    model = Map


class CompetitorAdmin(admin.ModelAdmin):
    inlines = [
    #    RouteSectionInlineAdmin,
    ]
    list_display = ('name', 'short_name', 'competition', 'start_time',
                    'access_code', 'approved')
    fieldsets = (
        (None, {
            'fields': ('name', 'short_name', )
        }),
        (_('Schedule'), {
            'fields': ('start_time', )
        }),
    )
    list_filter = ('competition__name', 'approved')
    actions = ['make_approved', 'renew_access_code']
    prepopulated_fields = {'short_name': ('name', ), }

    def make_approved(self, request, queryset):
        rows_updated = queryset.update(approved=True)
        if rows_updated == 1:
            message_bit = "1 competitor was"
        else:
            message_bit = "%s competitors were" % rows_updated
        self.message_user(request,
                          "%s successfully marked as approved." % message_bit)
    make_approved.short_description = _("Approve selected competitors")

    def renew_access_code(self, request, queryset):
        for competitor in queryset:
            competitor.reset_access_code()
            competitor.reset_api_token()
            competitor.save()
    renew_access_code.short_description = _("Issue new access codes")

    def get_queryset(self, request):
        qs = super(CompetitorAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(competition__publisher=request.user)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        else:
            return obj.competition.publisher == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        else:
            return obj.competition.publisher == request.user


class CompetitionAdmin(PublisherAdmin):
    list_display = ('name', 'start_date', 'end_date',
                    'timezone',
                    'publication_policy', 'signup_policy')
    fieldsets = (
        (None, {
            'fields': ('name', 'publication_policy', 'signup_policy')
        }),
        (_('Schedule'), {
            'fields': ('start_date', 'end_date', 'timezone')
        }),
    )
    inlines = [
        MapInlineAdmin,
        CompetitorInlineAdmin,
    ]

    class Media:
        js = {
            "//cdnjs.cloudflare.com/ajax/libs/moment.js/2.5.1/moment.min.js",
            "seuranta/js/jstz-1.0.5.min.js",
            "seuranta/admin/js/competition.js",
        }

admin.site.register(Competition, CompetitionAdmin)
admin.site.register(Competitor, CompetitorAdmin)
