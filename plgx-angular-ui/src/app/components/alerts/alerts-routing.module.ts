import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { AlertsComponent } from './alerts.component';
import { AlertDataComponent } from './alert-data/alert-data.component';


const routes: Routes = [
  {
    path: '',
    component: AlertsComponent, 
  },
  {
    path: '',
    children: [{
      path:':id/:alert-data',component: AlertDataComponent,
    },
    {
      path:':id', component:AlertsComponent
    },
  ]
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AlertsRoutingModule { }
