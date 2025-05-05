import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-metrics-card',
  template: `
    <mat-card class="metric-card" [ngStyle]="{'border-top': '3px solid ' + color}">
      <mat-card-content>
        <div class="metric-content">
          <div class="metric-icon" [ngStyle]="{'background-color': color}">
            <mat-icon>{{icon}}</mat-icon>
          </div>
          <div class="metric-info">
            <h3 class="metric-title">{{title}}</h3>
            <div class="metric-value-container">
              <p class="metric-value">{{value}}</p>
              <span *ngIf="subtitle" class="metric-subtitle">{{subtitle}}</span>
            </div>
          </div>
        </div>
      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    .metric-card {
      width: 260px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      transition: transform 0.3s, box-shadow 0.3s;
    }
    .metric-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }
    .metric-content {
      display: flex;
      align-items: center;
    }
    .metric-icon {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 50px;
      height: 50px;
      border-radius: 50%;
      margin-right: 16px;
    }
    .metric-icon mat-icon {
      color: white;
    }
    .metric-info {
      display: flex;
      flex-direction: column;
    }
    .metric-title {
      font-size: 14px;
      color: #666;
      margin: 0;
      margin-bottom: 4px;
    }
    .metric-value-container {
      display: flex;
      align-items: baseline;
    }
    .metric-value {
      font-size: 24px;
      font-weight: bold;
      margin: 0;
    }
    .metric-subtitle {
      font-size: 14px;
      color: #666;
      margin-left: 6px;
    }
  `]
})
export class MetricsCardComponent {
  @Input() title: string = '';
  @Input() value: string | number = '';
  @Input() subtitle: string = '';
  @Input() icon: string = 'info';
  @Input() color: string = '#5AA454';
}
