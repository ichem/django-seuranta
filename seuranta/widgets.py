from django import forms


class Base58UuidWidget(forms.TextInput):
    class Media(forms.Media):
        js = ()
        css = {
            'all': ()
        }

    def __init__(self, attrs=None):
        final_attrs = {'class': 'vBase58UuidField', 'max-size': 22,
                       'size': 25, 'readonly': 'readonly'}
        if attrs is not None:
            final_attrs.update(attrs)
        super(Base58UuidWidget, self).__init__(final_attrs)


class Base64UuidWidget(forms.TextInput):
    class Media(forms.Media):
        js = ()
        css = {
            'all': ()
        }

    def __init__(self, attrs=None):
        final_attrs = {
            'class': 'vBase64UuidField',
            'max-size': 22,
            'size': 25,
        }
        if attrs is not None:
            final_attrs.update(attrs)
        super(Base64UuidWidget, self).__init__(final_attrs)
