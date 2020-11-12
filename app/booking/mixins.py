class FeeGetQuerysetMixin:
    """
    Class, that provides custom get_queryset() method,
    returns objects connected only to users company.
    """

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(surcharge__company=user.companies.first())
