import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SearchService {
  private resultsSubject = new BehaviorSubject<{ path: string; url: string; distance: number }[]>([]);
  public results$ = this.resultsSubject.asObservable();

  setResults(results: { path: string; url: string; distance: number }[]) {
    console.log('SearchService setResults:', results);
    this.resultsSubject.next(results);
  }

  clearResults() {
    this.resultsSubject.next([]);
  }
}
