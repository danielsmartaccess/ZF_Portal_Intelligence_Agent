import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = '/api';

  constructor(private http: HttpClient) { }

  // Obter métricas do dashboard
  getMetrics(): Observable<any> {
    return this.http.get(`${this.baseUrl}/metrics`).pipe(
      catchError(this.handleError('getMetrics', {
        total_contacts: 125,
        total_interactions: 340,
        conversion_rate: '27%',
        average_response_time: '4h 20min'
      }))
    );
  }

  // Obter lista de contatos
  getContacts(page: number = 0, pageSize: number = 10): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/contacts?page=${page}&size=${pageSize}`).pipe(
      catchError(this.handleError('getContacts', [
        {
          id: 1,
          name: 'João Silva',
          company: 'Tech Solutions Ltda',
          position: 'Diretor de Tecnologia',
          email: 'joao.silva@techsolutions.com',
          phone: '(11) 99999-8888',
          lastInteraction: new Date('2025-05-04'),
          status: 'Ativo'
        },
        {
          id: 2,
          name: 'Maria Oliveira',
          company: 'Inovação Digital S.A.',
          position: 'CEO',
          email: 'maria.oliveira@inovacaodigital.com',
          phone: '(11) 98888-7777',
          lastInteraction: new Date('2025-05-02'),
          status: 'Pendente'
        },
        {
          id: 3,
          name: 'Carlos Santos',
          company: 'Global Soluções',
          position: 'Gerente de Vendas',
          email: 'carlos.santos@globalsolutions.com',
          phone: '(11) 97777-6666',
          lastInteraction: new Date('2025-05-01'),
          status: 'Ativo'
        },
        {
          id: 4,
          name: 'Ana Pereira',
          company: 'Nexus Tecnologia',
          position: 'Diretora de Marketing',
          email: 'ana.pereira@nexus.com',
          phone: '(11) 96666-5555',
          lastInteraction: new Date('2025-04-30'),
          status: 'Novo'
        },
        {
          id: 5,
          name: 'Roberto Lima',
          company: 'Future Systems',
          position: 'CTO',
          email: 'roberto.lima@futuresystems.com',
          phone: '(11) 95555-4444',
          lastInteraction: new Date('2025-04-28'),
          status: 'Inativo'
        }
      ]))
    );
  }

  // Obter detalhes de um contato específico
  getContactDetails(id: number): Observable<any> {
    return this.http.get(`${this.baseUrl}/contacts/${id}`).pipe(
      catchError(this.handleError('getContactDetails', null))
    );
  }

  // Obter empresas
  getCompanies(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/companies`).pipe(
      catchError(this.handleError('getCompanies', []))
    );
  }

  // Obter histórico de mensagens
  getMessages(contactId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/messages/${contactId}`).pipe(
      catchError(this.handleError('getMessages', []))
    );
  }

  /**
   * Manipulador de erro que permite à aplicação continuar funcionando
   * retornando um resultado padrão (mockado) se ocorrer um erro.
   */
  private handleError<T>(operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {
      console.error(`${operation} falhou: ${error.message}`);
      
      // Retorna um resultado mockado para manter a aplicação funcionando
      return of(result as T);
    };
  }
}
