from django.contrib import admin

from seuranta.models import Competition, Competitor, RouteSection


class PublisherAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if obj.publisher_id is None:
            obj.publisher = request.user
        obj.save()

    def queryset(self, request):
        qs = super(PublisherAdmin, self).queryset(request)
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


class CompetitorInlineAdmin(admin.TabularInline):
    model = Competitor
    prepopulated_fields = {'shortname': ('name',), }


class CompetitorAdmin(admin.ModelAdmin):
    inlines = [
        RouteSectionInlineAdmin,
    ]
    list_display = ('name', 'shortname', 'competition', 'starting_time',
                    'tracker', 'quick_setup_code', 'approved')
    actions = ['make_approved']

    def make_approved(self, request, queryset):
        rows_updated = queryset.update(approved=True)
        if rows_updated == 1:
            message_bit = "1 competitor was"
        else:
            message_bit = "%s competitors were" % rows_updated
        self.message_user(request,
                          "%s successfully marked as approved." % message_bit)
    make_approved.short_description = "Mark selected competitors as approved"

    def queryset(self, request):
        qs = super(CompetitorAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(competition__publisher=request.user)

    def has_add_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        else:
            return obj.competition.publisher == request.user

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
    list_display = ('name', 'opening_date', 'closing_date',
                    'publication_policy', 'signup_policy')
    inlines = [
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
