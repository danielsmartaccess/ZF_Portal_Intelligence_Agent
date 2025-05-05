import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  template: `
    <div class="app-container">
      <mat-toolbar color="primary" class="toolbar">
        <button mat-icon-button (click)="sidenav.toggle()">
          <mat-icon>menu</mat-icon>
        </button>
        <span>ZF Portal Intelligence Agent</span>
        <span class="toolbar-spacer"></span>
        <button mat-icon-button>
          <mat-icon>notifications</mat-icon>
        </button>
        <button mat-icon-button>
          <mat-icon>account_circle</mat-icon>
        </button>
      </mat-toolbar>

      <mat-sidenav-container class="sidenav-container">
        <mat-sidenav #sidenav mode="side" opened class="sidenav">
          <mat-nav-list>
            <a mat-list-item routerLink="/">
              <mat-icon>dashboard</mat-icon>
              <span class="nav-label">Dashboard</span>
            </a>
            <a mat-list-item>
              <mat-icon>people</mat-icon>
              <span class="nav-label">Contatos</span>
            </a>
            <a mat-list-item>
              <mat-icon>business</mat-icon>
              <span class="nav-label">Empresas</span>
            </a>
            <a mat-list-item>
              <mat-icon>chat</mat-icon>
              <span class="nav-label">Mensagens</span>
            </a>
            <a mat-list-item>
              <mat-icon>settings</mat-icon>
              <span class="nav-label">Configurações</span>
            </a>
          </mat-nav-list>
        </mat-sidenav>
        <mat-sidenav-content class="content">
          <router-outlet></router-outlet>
        </mat-sidenav-content>
      </mat-sidenav-container>
    </div>
  `,
  styles: [`
    .app-container {
      display: flex;
      flex-direction: column;
      height: 100vh;
    }
    .toolbar {
      position: fixed;
      z-index: 2;
    }
    .toolbar-spacer {
      flex: 1 1 auto;
    }
    .sidenav-container {
      flex: 1;
      margin-top: 64px;
    }
    .sidenav {
      width: 250px;
    }
    .nav-label {
      margin-left: 8px;
    }
    .content {
      padding: 20px;
    }
    mat-icon {
      margin-right: 8px;
    }
  `]
})
export class AppComponent {
  title = 'ZF Portal Intelligence Agent';
}
