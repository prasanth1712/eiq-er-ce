import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { AlertsComponent } from './alerts.component';


const routes: Routes = [
  {
    path: '',
      children: [
        {path: '', component: AlertsComponent},
        // {path: '//alerts', component: AlertsComponent},
        // {path: '/er-rules/alerts', component: AlertsComponent}
        ]
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AlertsRoutingModule { }
