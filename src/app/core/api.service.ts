import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) { }

  getAlerts(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/alerts`);
  }

  getHistory(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/history`);
  }

  processAlert(alertData: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/process_alert`, alertData);
  }

  retrain(): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/retrain`, {});
  }
}
