import { Component, OnInit, Input, ViewChild } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';

@Component({
  selector: 'app-contact-table',
  template: `
    <div class="table-container">
      <div *ngIf="loading" class="loading-spinner">
        <mat-spinner diameter="50"></mat-spinner>
      </div>

      <div *ngIf="!loading">
        <mat-form-field appearance="outline" class="search-field">
          <mat-label>Buscar contato</mat-label>
          <input matInput (keyup)="applyFilter($event)" placeholder="Nome, empresa, cargo..." #input>
          <mat-icon matSuffix>search</mat-icon>
        </mat-form-field>

        <div class="mat-elevation-z2 table-wrapper">
          <table mat-table [dataSource]="dataSource" matSort>
            
            <!-- Avatar Column -->
            <ng-container matColumnDef="avatar">
              <th mat-header-cell *matHeaderCellDef></th>
              <td mat-cell *matCellDef="let contact"> 
                <div class="avatar-container">
                  <div class="avatar">
                    {{ getInitials(contact.name) }}
                  </div>
                </div>
              </td>
            </ng-container>

            <!-- Name Column -->
            <ng-container matColumnDef="name">
              <th mat-header-cell *matHeaderCellDef mat-sort-header> Nome </th>
              <td mat-cell *matCellDef="let contact"> 
                <div class="contact-info">
                  <div class="contact-name">{{ contact.name }}</div>
                  <div class="contact-company">{{ contact.company }}</div>
                </div>
              </td>
            </ng-container>

            <!-- Position Column -->
            <ng-container matColumnDef="position">
              <th mat-header-cell *matHeaderCellDef mat-sort-header> Cargo </th>
              <td mat-cell *matCellDef="let contact"> {{ contact.position }} </td>
            </ng-container>

            <!-- Last Interaction Column -->
            <ng-container matColumnDef="lastInteraction">
              <th mat-header-cell *matHeaderCellDef mat-sort-header> Última Interação </th>
              <td mat-cell *matCellDef="let contact"> {{ contact.lastInteraction | date:'dd/MM/yyyy' }} </td>
            </ng-container>

            <!-- Status Column -->
            <ng-container matColumnDef="status">
              <th mat-header-cell *matHeaderCellDef mat-sort-header> Status </th>
              <td mat-cell *matCellDef="let contact"> 
                <span class="status-badge" [ngClass]="'status-' + contact.status.toLowerCase()">
                  {{ contact.status }}
                </span>
              </td>
            </ng-container>

            <!-- Actions Column -->
            <ng-container matColumnDef="actions">
              <th mat-header-cell *matHeaderCellDef></th>
              <td mat-cell *matCellDef="let contact">
                <button mat-icon-button [matMenuTriggerFor]="menu">
                  <mat-icon>more_vert</mat-icon>
                </button>
                <mat-menu #menu="matMenu">
                  <button mat-menu-item>
                    <mat-icon>visibility</mat-icon>
                    <span>Ver detalhes</span>
                  </button>
                  <button mat-menu-item>
                    <mat-icon>edit</mat-icon>
                    <span>Editar</span>
                  </button>
                  <button mat-menu-item>
                    <mat-icon>chat</mat-icon>
                    <span>Enviar mensagem</span>
                  </button>
                </mat-menu>
              </td>
            </ng-container>

            <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
            <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>

            <!-- Row shown when no matching data -->
            <tr class="mat-row" *matNoDataRow>
              <td class="mat-cell" colspan="6">Nenhum contato encontrado com "{{input.value}}"</td>
            </tr>
          </table>

          <mat-paginator [pageSizeOptions]="[5, 10, 25, 100]" aria-label="Selecione a página"></mat-paginator>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .table-container {
      position: relative;
    }
    .loading-spinner {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 200px;
    }
    .search-field {
      width: 100%;
      margin-bottom: 20px;
    }
    .table-wrapper {
      overflow-x: auto;
    }
    table {
      width: 100%;
    }
    .avatar-container {
      display: flex;
      align-items: center;
    }
    .avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background-color: #3f51b5;
      color: white;
      display: flex;
      justify-content: center;
      align-items: center;
      font-weight: bold;
    }
    .contact-info {
      display: flex;
      flex-direction: column;
    }
    .contact-name {
      font-weight: 500;
    }
    .contact-company {
      font-size: 12px;
      color: #666;
    }
    .status-badge {
      padding: 6px 12px;
      border-radius: 16px;
      font-size: 12px;
      font-weight: 500;
    }
    .status-ativo {
      background-color: #e6f7e6;
      color: #2e7d32;
    }
    .status-inativo {
      background-color: #ffebee;
      color: #c62828;
    }
    .status-pendente {
      background-color: #fff8e1;
      color: #f57f17;
    }
    .status-novo {
      background-color: #e3f2fd;
      color: #1565c0;
    }
  `]
})
export class ContactTableComponent implements OnInit {
  @Input() set contacts(data: any[]) {
    if (data && data.length > 0) {
      this._contacts = data;
      this.dataSource = new MatTableDataSource(this._contacts);
      this.dataSource.paginator = this.paginator;
      this.dataSource.sort = this.sort;
      this.loading = false;
    }
  }
  get contacts(): any[] {
    return this._contacts;
  }

  private _contacts: any[] = [];
  displayedColumns: string[] = ['avatar', 'name', 'position', 'lastInteraction', 'status', 'actions'];
  dataSource!: MatTableDataSource<any>;
  loading: boolean = true;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor() { }

  ngOnInit(): void {
    // Inicializar com dados vazios até que os contatos sejam carregados
    this.dataSource = new MatTableDataSource(this._contacts);
  }

  ngAfterViewInit() {
    if (this.dataSource) {
      this.dataSource.paginator = this.paginator;
      this.dataSource.sort = this.sort;
    }
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();

    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  getInitials(name: string): string {
    if (!name) return '';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
  }
}
