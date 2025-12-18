interface ApiSearchResponse {
  query: string;
  results: { path: string; url: string; distance: number }[];
}

interface SearchResult {
  path: string;
  url: string;
  distance: number;
}