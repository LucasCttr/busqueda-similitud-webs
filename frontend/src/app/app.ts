import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { UploadComponent } from './upload/upload.component';
import { SearchComponent } from './search/search.component';
import { SearchResultsComponent } from './results/search-results.component';

@Component({
  selector: 'app-root',
  imports: [ UploadComponent, SearchComponent, SearchResultsComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('Image Search App');
}
