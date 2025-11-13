import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Database {
  name: string;
}

export interface Table {
  name: string;
  database: string;
}

export interface QueryRequest {
  query: string;
  database?: string;
}

export interface QueryResult {
  columns: string[];
  rows: any[][];
  row_count: number;
  execution_time: number;
  bytes_scanned: number;
  query_execution_id: string;
}

export interface SystemSettings {
  athena_max_download_rows: number;
  athena_display_rows: number;
}

@Injectable({
  providedIn: 'root'
})
export class AthenaService {
  private readonly baseUrl = `${environment.apiUrl}/athena`;

  constructor(private http: HttpClient) {}

  // Database operations
  listDatabases(): Observable<Database[]> {
    return this.http.get<Database[]>(`${this.baseUrl}/databases`);
  }

  listTables(database: string): Observable<Table[]> {
    return this.http.get<Table[]>(`${this.baseUrl}/databases/${database}/tables`);
  }

  // Query operations
  executeQuery(request: QueryRequest): Observable<QueryResult> {
    return this.http.post<QueryResult>(`${this.baseUrl}/query`, request);
  }

  downloadQueryResults(request: QueryRequest): Observable<Blob> {
    return this.http.post(`${this.baseUrl}/query/download`, request, {
      responseType: 'blob'
    });
  }

  // Admin operations
  getAdminSettings(): Observable<SystemSettings> {
    return this.http.get<SystemSettings>(`${this.baseUrl}/admin/settings`);
  }

  updateDownloadLimit(limit: number): Observable<{ message: string; new_value: number }> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.put<{ message: string; new_value: number }>(
      `${this.baseUrl}/admin/settings/download-limit`,
      null,
      { params }
    );
  }

  updateDisplayLimit(limit: number): Observable<{ message: string; new_value: number }> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.put<{ message: string; new_value: number }>(
      `${this.baseUrl}/admin/settings/display-limit`,
      null,
      { params }
    );
  }

  // Query history (if we add this later)
  getQueryHistory(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/history`);
  }
}
