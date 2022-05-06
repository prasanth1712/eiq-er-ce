// import { NgModule } from '@angular/core';
// import { CommonModule } from '@angular/common';
// import { RouterModule } from '@angular/router';
// import { DashboardComponent} from './dashboard.component';
// import { AdminContentComponent } from './admin-content/admin-content.component';
// import { AdminAsideComponent } from '../layout/admin-aside/admin-aside.component';

// import { HostsComponent} from './hosts/hosts.component';
// import { ManagementComponent} from './management/management.component';
// import { ChangePasswordComponent} from './management/change-password/change-password.component';
// import { ConfigureEmailComponent} from './management/configure-email/configure-email.component';
// import { PurgeDataComponent} from './management/purge-data/purge-data.component';
// import { IntelKeysComponent} from './management/intel-keys/intel-keys.component';
// import { AlertsComponent} from './alerts/alerts.component';
// import { AlertDataComponent} from './alerts/alert-data/alert-data.component';
// import { LiveQueriesComponent} from './live-queries/live-queries.component';
// import { IocComponent} from './ioc/ioc.component';
// import { RuleComponent} from './rule/rule.component';
// import { AddRuleComponent } from './rule/add-rule/add-rule.component';
// import { EditRuleComponent } from './rule/edit-rule/edit-rule.component';
// import { TagComponent} from './tag/tag.component';
// import { CarvesComponent} from './carves/carves.component';
// import { YaraComponent} from './yara/yara.component';
// import { HuntComponent} from './hunt/hunt.component';
// import { ConfigComponent} from './config/config.component';
// import { PacksComponent} from './packs/packs.component';
// import { UpdateQueryInPacksComponent } from './packs/update-query-in-packs/update-query-in-packs.component';
// import { QueriesComponent} from './queries/queries.component';
// import { AddQueryComponent } from './queries/add-query/add-query.component';
// import { UpdateQueriesInQueriesComponent } from './queries/update-queries-in-queries/update-queries-in-queries.component';
// import { OptionsComponent} from './options/options.component';
// import { SearchComponent} from './search/search.component';
// import { LogoutComponent} from '../logout/logout.component';
// import { NodesComponent } from './hosts/nodes/nodes.component';
// import { NodeFilterComponent} from './node-filter/node-filter.component';
// import { ActivityComponent } from './hosts/nodes/activity/activity.component';
// import { QueryComponent} from './query/query.component';
// import { QueryUpdateComponent} from './query-update/query-update.component';
// import { Openc2Component} from './openc2/openc2.component';
// import { AddOpenc2Component} from './openc2/add-openc2/add-openc2.component';
// import { TaggedComponent } from './tag/tagged/tagged.component';
// import { TestComponent } from './test/test.component';


// @NgModule({
//   declarations: [],
//   imports: [
//     RouterModule.forChild([
//       {
//         path: 'manage',
//         component: DashboardComponent,
//         children:[
//           {
//             path:'',
//             component: AdminContentComponent
//           },
//           {
//             path:'hosts',
//             component: HostsComponent
//             },

//           {
//             path: 'hosts/nodes/:id',
//             component: NodesComponent

//             },
//             {
//               path: 'node-filter/:id/:value',
//               component: NodeFilterComponent

//               },
//             {
//             path: 'hosts/nodes/activity/:id',
//             component: ActivityComponent

//             },
//             {
//               path:'openc2',
//               component: Openc2Component
//               },
//             {
//               path:'add-openc2',
//               component: AddOpenc2Component
//               },

//           {
//             path:'change-password',
//             component: ChangePasswordComponent
//           },
//           {
//             path:'configure-email',
//             component: ConfigureEmailComponent
//           },
//           {
//             path:'purge-data',
//             component: PurgeDataComponent
//           },
//           {
//             path:'intel-keys',
//             component: IntelKeysComponent
//           },
//           {
//             path:'alerts',
//             component: AlertsComponent
//           },
//           {
//             path:'alerts',
//             component: AlertsComponent
//           },
//           {
//             path:'alerts/alert-data/:id',
//             component: AlertDataComponent
//           },
//           {
//             path:'live-queries',
//             component: LiveQueriesComponent
//           },
//           {
//             path:'ioc',
//             component: IocComponent
//           },
//           {
//             path:'rule',
//             component: RuleComponent
//           },
//           {
//             path:'rule/add-rule',
//             component: AddRuleComponent
//           },
//           {
//             path:'rule/edit-rule/:id',
//             component: EditRuleComponent
//           },
//           {
//             path:'tag',
//             component: TagComponent
//           },
//           {
//             path:'test',
//             component: TestComponent
//           },
//           {
//             path:'tagged/:value',
//             component: TaggedComponent
//             },
//           {
//             path:'carves',
//             component: CarvesComponent
//           },
//           {
//             path:'yara',
//             component: YaraComponent
//           },
//           {
//             path:'hunt',
//             component: HuntComponent
//           },
//           {
//             path:'config',
//             component: ConfigComponent
//           },
//           {
//             path:'packs',
//             component: PacksComponent
//           },
//           {
//             path:'packs/update-query-in-packs/:id',
//             component: UpdateQueryInPacksComponent
//           },
//           {
//             path:'queries',
//             component: QueriesComponent
//           },
//           {
//             path:'queries/add-query',
//             component: AddQueryComponent
//           },
//           {
//             path:'queries/update-queries-in-queries/:id',
//             component: UpdateQueriesInQueriesComponent
//           },
//           {
//             path:'query',
//             component: QueryComponent
//           },
//           {
//             path:'query-update/:id',
//             component: QueryUpdateComponent
//           },
//           {
//             path:'options',
//             component: OptionsComponent
//           },
//           {
//             path:'search',
//             component: SearchComponent
//           },
//           {
//             path:'logout',
//             component: LogoutComponent
//           }

//         ]
//       }

//     ])
//   ],
//   exports:[RouterModule]
// })
// export class DashbordRoutingModule { }


import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { DashboardComponent } from './dashboard.component';

const routes: Routes = [
  {
    path: '',
    component: DashboardComponent,
  }]


@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})

export class DashbordRoutingModule { }

