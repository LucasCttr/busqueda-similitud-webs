import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.css']
})
export class UploadComponent implements OnDestroy {
  selectedFile: File | null = null;
  previewUrl: string | null = null;
  uploadStatus: string = '';
  isUploading: boolean = false;
  
  constructor(private http: HttpClient) {}

  onFileSelected(event: any) {
    const file = event.target.files[0];
    // revoke previous preview if any
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
      this.previewUrl = null;
    }

    if (file && file.type.startsWith('image/')) {
      this.selectedFile = file;
      // create an object URL for preview
      this.previewUrl = URL.createObjectURL(file);
      this.uploadStatus = `Archivo seleccionado: ${file.name}`;
    } else {
      this.uploadStatus = 'Por favor selecciona una imagen válida';
      this.selectedFile = null;
      this.previewUrl = null;
    }
  }

  onUpload() {
    if (!this.selectedFile) {
      this.uploadStatus = 'No hay archivo seleccionado';
      return;
    }

    this.isUploading = true;
    const formData = new FormData();
    formData.append('file', this.selectedFile);

    this.http.post('http://localhost:8000/upload', formData).subscribe({
      next: (response: any) => {
        this.uploadStatus = `Imagen subida exitosamente: ${response.filename}`;
        this.isUploading = false;
        this.selectedFile = null;
        if (this.previewUrl) {
          URL.revokeObjectURL(this.previewUrl);
          this.previewUrl = null;
        }
      },
      error: (error) => {
        this.uploadStatus = `Error al subir la imagen: ${error.message}`;
        this.isUploading = false;
      }
    });
  }

  clearUpload(): void {
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
    }
    this.selectedFile = null;
    this.previewUrl = null;
    this.uploadStatus = '';
    this.isUploading = false;
  }

  ngOnDestroy(): void {
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
      this.previewUrl = null;
    }
  }
}
