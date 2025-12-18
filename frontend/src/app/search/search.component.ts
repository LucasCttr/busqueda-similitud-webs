import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { SearchService } from '../services/search.service';

interface ApiSearchResponse {
  query: string;
  results: { path: string; url: string; distance: number }[];
}

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css']
})
export class SearchComponent {
  selectedFile: File | null = null;
  isSearching = false;
  searchStatus = '';
  previewUrl: string | null = null;
  radius = 1;
  showPreview = false;

  ngOnInit() {
    // Permitir pegar imágenes desde el portapapeles
    window.addEventListener('paste', this.handlePaste as EventListener);
  }

  ngOnDestroy() {
    window.removeEventListener('paste', this.handlePaste as EventListener);
  }

  handlePaste = (event: ClipboardEvent) => {
    if (event.clipboardData) {
      const items = event.clipboardData.items;
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile();
          if (file) {
            this.selectedFile = file;
            this.searchStatus = '';
            const reader = new FileReader();
            reader.onload = (e: any) => {
              this.previewUrl = e.target.result;
            };
            reader.readAsDataURL(file);
            this.showPreview = false;
            event.preventDefault();
            break;
          }
        }
      }
    }
  }

  constructor(private http: HttpClient, private searchService: SearchService) {}

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      this.selectedFile = file;
      this.searchStatus = '';
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.previewUrl = e.target.result;
      };
      reader.readAsDataURL(file);
      this.showPreview = false;
    } else {
      this.searchStatus = 'Por favor selecciona una imagen válida';
      this.selectedFile = null;
      this.previewUrl = null;
    }
  }

  onSearch() {
    if (!this.selectedFile) {
      this.searchStatus = 'No hay archivo seleccionado';
      return;
    }

    this.isSearching = true;
    const formData = new FormData();
    formData.append('file', this.selectedFile);
    formData.append('radius', String(this.radius));
    formData.append('k', '10');

    this.http.post<ApiSearchResponse>('http://localhost:8000/search', formData).subscribe({
      next: (data) => {
        console.log('SearchComponent recibió del backend:', data);
        console.log('Enviando resultados al servicio:', data.results);
        this.searchService.setResults(data.results);
        this.isSearching = false;
        this.searchStatus = data.results.length > 0
          ? `Se encontraron ${data.results.length} imágenes similares`
          : 'No se encontraron imágenes similares';
      },
      error: (error) => {
        this.searchStatus = `Error en la búsqueda: ${error.message}`;
        this.isSearching = false;
      }
    });
  }

  clearSearch() {
    this.selectedFile = null;
    this.searchService.clearResults();
    this.searchStatus = '';
    this.previewUrl = null;
    this.radius = 1;
    this.showPreview = false;
  }

  openPreview() {
    if (this.previewUrl) {
      this.showPreview = true;
    }
  }

  closePreview() {
    this.showPreview = false;
  }
}
