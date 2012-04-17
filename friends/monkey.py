# xxx: ask Euan for some comments and docstrings

from django.http import HttpResponseRedirect
from django.views.generic.edit import ProcessFormView, ModelFormMixin

#------------------------------------------------------------------------------
ProcessFormView.init_needs_request = False
ProcessFormView.save_needs_request = False

#------------------------------------------------------------------------------        
def get_form_kwargs(self):
    kwargs = super(ModelFormMixin, self).get_form_kwargs()
    kwargs.update({'instance': self.object})
    if self.init_needs_request:
        kwargs.update({'request': self.request})
    return kwargs

#------------------------------------------------------------------------------
def form_valid(self, form):
    if self.save_needs_request:
        self.object = form.save(self.request)
    else: 
        self.object = form.save()
    if self.success_url:
        redirect_url = self.success_url % self.object.__dict__
        return HttpResponseRedirect(redirect_url)
    else:
        return self.render_to_response(self.get_context_data(form=form))

#------------------------------------------------------------------------------
#ModelFormMixin.get_form_kwargs = get_form_kwargs
#ModelFormMixin.form_valid = form_valid
