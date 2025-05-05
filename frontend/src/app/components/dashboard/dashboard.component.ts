import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-dashboard',
  template: `
    <div class="dashboard-container">
      <div class="dashboard-header">
        <h1>Conversion Dashboard</h1>
      </div>
      
      <div class="metrics-row">
        <app-metrics-card
          title="Contacts Identified"
          value="120"
          icon="people"
          color="#26a69a">
        </app-metrics-card>

        <app-metrics-card
          title="Average Interactions"
          value="4,5"
          subtitle="per contact"
          icon="build"
          color="#42a5f5">
        </app-metrics-card>

        <app-metrics-card
          title="Promoted Portal"
          value="37"
          icon="check_circle"
          color="#ffa726">
        </app-metrics-card>

        <app-metrics-card
          title="Time to Conversion"
          value="12,4"
          subtitle="days"
          icon="schedule"
          color="#7e57c2">
        </app-metrics-card>
      </div>

      <div class="charts-row">
        <mat-card class="chart-card">
          <mat-card-header>
            <mat-card-title>Contacts Identified by Role</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <ngx-charts-bar-vertical
              [view]="chartView"
              [scheme]="colorScheme"
              [results]="roleData"
              [gradient]="false"
              [xAxis]="true"
              [yAxis]="true"
              [showXAxisLabel]="false"
              [showYAxisLabel]="false">
            </ngx-charts-bar-vertical>
          </mat-card-content>
        </mat-card>

        <mat-card class="chart-card">
          <mat-card-header>
            <mat-card-title>Contacts Identified & Converted</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <ngx-charts-line-chart
              [view]="chartView"
              [scheme]="colorScheme"
              [results]="conversionTrendsData"
              [gradient]="false"
              [xAxis]="true"
              [yAxis]="true"
              [showXAxisLabel]="false"
              [showYAxisLabel]="false"
              [legend]="true">
            </ngx-charts-line-chart>
          </mat-card-content>
        </mat-card>
      </div>

      <div class="table-row">
        <mat-card>
          <mat-card-header>
            <mat-card-title>Recent interactions</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <app-contact-table [contacts]="recentInteractions"></app-contact-table>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: 20px;
    }
    .dashboard-header {
      margin-bottom: 24px;
    }
    .dashboard-header h1 {
      font-size: 24px;
      font-weight: 500;
      color: #333;
      margin: 0;
    }
    .metrics-row {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 24px;
    }
    .charts-row {
      display: flex;
      flex-wrap: wrap;
      gap: 24px;
      margin-bottom: 24px;
    }
    .chart-card {
      flex: 1;
      min-width: 45%;
    }
    .table-row {
      margin-bottom: 24px;
    }
    mat-card {
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    mat-card-header {
      padding: 16px;
      border-bottom: 1px solid #eee;
    }
    mat-card-title {
      font-size: 16px;
      font-weight: 500;
      margin: 0;
    }
    mat-card-content {
      padding: 16px;
    }
  `]
})
export class DashboardComponent implements OnInit {
  recentInteractions: any[] = [];
  chartView: [number, number] = [500, 300];
  
  roleData: any[] = [
    { name: 'Finance Manager', value: 65 },
    { name: 'Treasury Manager', value: 57 },
    { name: 'CFO', value: 45 }
  ];

  conversionTrendsData: any[] = [
    {
      name: 'Identified',
      series: [
        { name: 'Mar', value: 23 },
        { name: 'Apr', value: 32 },
        { name: 'May', value: 44 },
        { name: 'Jun', value: 52 },
        { name: 'Jul', value: 75 },
        { name: 'Aug', value: 68 },
        { name: 'Sep', value: 71 }
      ]
    },
    {
      name: 'Converted',
      series: [
        { name: 'Mar', value: 10 },
        { name: 'Apr', value: 17 },
        { name: 'May', value: 26 },
        { name: 'Jun', value: 28 },
        { name: 'Jul', value: 48 },
        { name: 'Aug', value: 59 },
        { name: 'Sep', value: 68 }
      ]
    }
  ];

  colorScheme: any = {
    domain: ['#42a5f5', '#26a69a', '#ffa726', '#7e57c2']
  };

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    this.loadRecentInteractions();
  }

  loadRecentInteractions(): void {
    // Dados mockados para recentes interações
    this.recentInteractions = [
      {
        id: 1,
        name: 'João Silva',
        company: 'Tech Solutions Ltda',
        position: 'Finance Manager',
        lastInteraction: new Date('2024-08-15'),
        status: 'Promoted Portal',
        messagesCount: 4
      },
      {
        id: 2,
        name: 'Tatiane Souza',
        company: 'Inovação Digital S.A.',
        position: 'CFO',
        lastInteraction: new Date('2024-08-15'),
        status: 'Follow-up Sent',
        messagesCount: 3
      },
      {
        id: 3,
        name: 'Lucas Fernandes',
        company: 'Global Soluções',
        position: 'Treasury Manager',
        lastInteraction: new Date('2024-08-14'),
        status: 'Initial Contact',
        messagesCount: 2
      }
    ];
  }
}
