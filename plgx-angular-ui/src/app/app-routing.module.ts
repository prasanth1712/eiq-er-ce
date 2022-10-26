import { NgModule } from '@angular/core';
import { Routes, RouterModule,  } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard.component';
import { GlobalComponent } from './global/global.component';
import {AuthGuard}  from './_helpers/auth.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full'
  },
  {
    path: 'authentication',
    loadChildren: () => import('./authentication/authentication.module').
      then(m => m.AuthenticationModule)
  },
  {
    path: '',
    component: GlobalComponent,
    canActivate: [AuthGuard],
    children: [{
      path: 'dashboard', loadChildren: () => import('./dashboard/dashboard.module').
        then(m => m.DashboardModule),
    },
    {
    path: 'manage', loadChildren: () => import('./dashboard/dashboard.module').
      then(m => m.DashboardModule),
    },
    {
      path: 'hosts', loadChildren: () => import('./components/hosts/hosts.module').
        then(m => m.HostsModule),
    },
    {
      path: 'settings', loadChildren: () => import('./components/management/management.module').
        then(m => m.ManagementModule),
    },
    {
      path: 'hostconfiguration', loadChildren: () => import('./components/hosts-configuration/hosts-configuration.module').
        then(m => m.HostsConfigurationModule),
    },
    {
      path: 'alerts', loadChildren: () => import('./widgets/alerts/alerts.module').
        then(m => m.AlertsModule),
    },
    {
      path: 'live-query', loadChildren: () => import('./components/live-queries/live-queries.module').
        then(m => m.LiveQueriesModule),
    },
    {
      path: 'rules', loadChildren: () => import('./components/rules/rules.module').
        then(m => m.RulesModule),
    },
    {
      path: 'carves', loadChildren: () => import('./components/carves/carves.module').
        then(m => m.CarvesModule),
    },
    {
      path: 'hunt', loadChildren: () => import('./components/hunt/hunt.module').
        then(m => m.HuntModule),
    },
    {
      path: 'profile', loadChildren: () => import('./components/user-profile/user-profile.module').
        then(m => m.UserProfileModule),
    },
    {
      path: 'search', loadChildren: () => import('./components/search/search.module').
        then(m => m.SearchModule),
    },
    {
      path: 'pagenotfound', loadChildren: () => import('./components/pagenotfound/pagenotfound.module').
        then(m => m.PagenotfoundModule),
    },
    {
      path: '**',
      loadChildren: () => import('./components/pagenotfound/pagenotfound.module').
        then(m => m.PagenotfoundModule),
    },
    ]
  },
  {
    path: '**',
    redirectTo: 'authentication',
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes,{ scrollPositionRestoration: 'enabled', relativeLinkResolution: 'legacy' })],
  exports: [RouterModule]
})
export class AppRoutingModule { }
