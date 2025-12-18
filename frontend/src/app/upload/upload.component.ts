import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.css']
})
export class UploadComponent {
  selectedFile: File | null = null;
  uploadStatus: string = '';
  isUploading: boolean = false;

  constructor(private http: HttpClient) {}

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      this.selectedFile = file;
      this.uploadStatus = `Archivo seleccionado: ${file.name}`;
    } else {
      this.uploadStatus = 'Por favor selecciona una imagen válida';
      this.selectedFile = null;
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
      },
      error: (error) => {
        this.uploadStatus = `Error al subir la imagen: ${error.message}`;
        this.isUploading = false;
      }
    });
  }
}
