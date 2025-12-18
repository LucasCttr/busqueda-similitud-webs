import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SearchService } from '../services/search.service';

@Component({
  selector: 'app-search-results',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './search-results.component.html',
  styleUrls: ['./search-results.component.css']
})
export class SearchResultsComponent implements OnInit {
  results: { path: string; url: string; distance: number }[] = [];
  selectedImage: { path: string; url: string; distance: number } | null = null;
  
  constructor(private searchService: SearchService) {}
  
  ngOnInit() {
    this.searchService.results$.subscribe(results => {
      console.log('SearchResultsComponent recibió resultados:', results);
      this.results = results;
    });
  }
  
  openImage(result: { path: string; url: string; distance: number }) {
    this.selectedImage = result;
  }
  
  closeImage() {
    this.selectedImage = null;
  }

  fileName(p: string): string {
    if (!p) return '';
    const norm = p.replace(/\\/g, '/');
    const parts = norm.split('/');
    return parts[parts.length - 1] || p;
  }
}