from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from seuranta.models import (Competition, Competitor, Route, Map,
                             CompetitorToken)


class PublisherAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if obj.publisher_id is None:
            obj.publisher = request.user
        obj.save()


class RouteInlineAdmin(admin.TabularInline):
    model = Route


class CompetitorInlineAdmin(admin.StackedInline):
    model = Competitor
    prepopulated_fields = {'short_name': ('name',), }


class MapInlineAdmin(admin.StackedInline):
    model = Map


class CompetitorAdmin(admin.ModelAdmin):
    inlines = [
        RouteInlineAdmin,
    ]
    list_display = ('name', 'short_name', 'competition', 'start_time',
                    'access_code', 'approved')
    fieldsets = (
        (None, {
            'fields': ('name', 'short_name', )
        }), (_('Schedule'), {
            'fields': ('start_time', )
        }), (_('Miscellaneous'), {
            'fields': ('access_code', )
        }),
    )
    list_filter = ('competition__name', 'approved')
    actions = ['make_approved', 'renew_access_code', 'merge_route_points']
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
            competitor.save()
    renew_access_code.short_description = _("Issue new access codes")

    def merge_route_points(self, request, queryset):
        for competitor in queryset:
            competitor.merge_route()
            competitor.save()
    merge_route_points.short_description = _("Merge Route Points")


class CompetitionAdmin(PublisherAdmin):
    list_display = ('name', 'start_date', 'end_date',
                    'timezone',
                    'publication_policy', 'signup_policy')
    fieldsets = (
        (None, {
            'fields': ('name', 'publication_policy', 'signup_policy',
                       'timezone', 'live_delay', )
        }),
        (_('Schedule'), {
            'fields': ('start_date', 'end_date', )
        }),
        (_('Location'), {
            'fields': ('latitude', 'longitude', 'zoom', )
        }),
    )
    inlines = [
        MapInlineAdmin,
        CompetitorInlineAdmin,
    ]
    actions = ['close']

    def close(self, request, queryset):
        for competition in queryset:
            competition.close_competition()
            competition.save()
        if len(queryset) == 1:
            message_bit = '1 competition was'
        else:
            message_bit = '%s competitions were' % len(queryset)
        self.message_user(request,
                          '%s successfully closed.' % message_bit)

    close.short_description = _('Close competitions')

    class Media:
        js = {
            "vendor/jstz/1.0.5/jstz-1.0.5.min.js",
            "seuranta/admin/js/competition.js",
        }


class CompetitorTokenAdmin(admin.ModelAdmin):
    list_display = ('key', 'competitor', 'created')
    fields = ('competitor',)
    ordering = ('-created',)


admin.site.register(CompetitorToken, CompetitorTokenAdmin)
admin.site.register(Competition, CompetitionAdmin)
admin.site.register(Competitor, CompetitorAdmin)
