from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from share_file.models import File

from django.views.generic.edit import FormView
from .forms import FileFieldForm


def home(request):
    return render(request, 'share_file/file_list.html', {'title': 'dfkdj'})


class FileList(LoginRequiredMixin, ListView):
    model = File
    template_name = "share_file/file_list.html"
    extra_context = {'title': 'Файлы'}
    context_object_name = 'files'
    paginate_by = 7


# class FileAdd(LoginRequiredMixin, CreateView):
#     model = File
#     form_class = FileForm
#     # extra_context = {'title': 'Добавить файл', 'files': File.objects.all()}
#     template_name = 'share_file/file_add.html'
#     success_url = reverse_lazy('share_file:file_list')
#
#     def get_context_data(self, **kwargs):
#         context =  super().get_context_data(**kwargs)
#         context['title'] = 'Добавить файл'
#         context['files'] = File.objects.all()
#         context['form'] = FileForm()
#         return context





class FileFieldFormView(FormView):
    form_class = FileFieldForm
    template_name = "share_file/file_add.html"  # Replace with your template.
    success_url = reverse_lazy("share_file:file_add") # Replace with your URL or reverse().

    def form_valid(self, form):
        files = form.cleaned_data["file_field"]
        for f in files:
            fl = File(file=f)
            fl.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['title'] = 'Файлы'
        context['files'] = File.objects.all()
        return context

def file_delete(request, pk):
    file = File.objects.get(pk=pk)
    file.file.delete()
    file.delete()
    return redirect('share_file:file_add')