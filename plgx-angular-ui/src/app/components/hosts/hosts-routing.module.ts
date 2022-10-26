import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { HostsComponent } from './hosts.component';
import { NodesComponent } from './nodes/nodes.component';
import { ActivityComponent } from './activity/activity.component';
import { AlertsComponent } from 'src/app/widgets/alerts/alerts.component';
// import { FilterAlertsWithHostnameComponent } from './filter-alerts-with-hostname/filter-alerts-with-hostname.component';

const routes: Routes = [
  {
    path: '',
    component: HostsComponent, 
  },
  {
    path: '',
    children: [{
      path: ':id', component: NodesComponent,
    }]
  },
  {
    path: '',
    children: [{
      path: ':id/activity', component: ActivityComponent,
    }]
  },
  {
    path: '',
    children: [{
      path: ':id/alerts', component: AlertsComponent,
    }]
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class HostsRoutingModule { }
