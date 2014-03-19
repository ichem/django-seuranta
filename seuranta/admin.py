from .models import Tracker, Competition, Competitor, RouteSection
from django.contrib import admin

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
	prepopulated_fields = {'shortname':('name',),}

class TrackerAdmin(PublisherAdmin):
	list_display = ('uuid', 'handle', 'pref_name', 'creation_date', 'last_seen')

class CompetitionAdmin(PublisherAdmin):
    list_display = ('uuid', 'name', '_utc_start_date', '_utc_end_date', 'map_format', "is_started", "is_completed", "is_current")

    inlines = [
        CompetitorInlineAdmin,
    ]

    class Media:
        js = {
            "seuranta/js/jstz-1.0.5.min.js",
            "seuranta/admin/js/competition.js"
        }

class CompetitorAdmin(admin.ModelAdmin):
	list_display = ('uuid', 'competition', 'name')
	inlines = [
        RouteSectionInlineAdmin,
    ]

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

admin.site.register(Tracker, TrackerAdmin)
admin.site.register(Competition, CompetitionAdmin)
admin.site.register(Competitor, CompetitorAdmin)
