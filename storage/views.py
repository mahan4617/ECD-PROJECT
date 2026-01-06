from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import UploadForm
from .models import StoredFile
from .utils import aes_encrypt, aes_decrypt, hide_data_in_image, extract_data_from_image
from django.core.files.base import ContentFile
from django.contrib import messages
import io

def landing_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')

@login_required
def dashboard_view(request):
    return render(request, 'storage/dashboard.html')

@login_required
def file_list_view(request):
    files = StoredFile.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'storage/file_list.html', {'files': files})

@login_required
def upload_view(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            up_file = form.cleaned_data['file']
            cover = form.cleaned_data['cover_image']
            data = up_file.read()
            ct, nonce = aes_encrypt(request.user.id, data)
            # ensure cover content is available for both PIL and model save
            if hasattr(cover, 'temporary_file_path'):
                cover_path = cover.temporary_file_path()
            else:
                cover.seek(0)
                cover_buf = io.BytesIO(cover.read())
                cover_path = cover_buf
                cover.seek(0)
            stego_img = hide_data_in_image(cover_path, ct)
            output = io.BytesIO()
            stego_img.save(output, format='PNG')
            output.seek(0)
            stego_content = ContentFile(output.read(), name=f"{up_file.name}.png")
            obj = StoredFile.objects.create(
                user=request.user,
                original_name=up_file.name,
                cover_image=cover,
                stego_image=stego_content,
                nonce=nonce,
                data_length=len(ct),
            )
            messages.success(request, 'File encrypted and hidden into the image successfully.')
            return redirect('file_list')
    else:
        form = UploadForm()
    return render(request, 'storage/upload.html', {'form': form})

@login_required
def download_view(request, pk: int):
    obj = get_object_or_404(StoredFile, pk=pk, user=request.user)
    obj.stego_image.open()
    buf = io.BytesIO(obj.stego_image.read())
    ct = extract_data_from_image(buf)
    data = aes_decrypt(request.user.id, bytes(obj.nonce), ct)
    resp = HttpResponse(data, content_type='application/octet-stream')
    resp['Content-Disposition'] = f'attachment; filename="{obj.original_name}"'
    return resp

# Create your views here.
