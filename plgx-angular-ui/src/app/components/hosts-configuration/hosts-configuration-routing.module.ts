import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ConfigComponent } from './config/config.component';
import { PacksComponent } from './packs/packs.component';
import { QueriesComponent } from './queries/queries.component';
import { UpdateQueryInPacksComponent } from './packs/update-query-in-packs/update-query-in-packs.component';
import { AddQueryComponent } from './queries/add-query/add-query.component';
import { UpdateQueriesInQueriesComponent } from './queries/update-queries-in-queries/update-queries-in-queries.component';
import { TagComponent } from './tag/tag.component';
import { TaggedComponent } from './tag/tagged/tagged.component';

const routes: Routes = [
  {
      path: '',
      children: [
          {
              path: 'configurations',
              component: ConfigComponent
          },
          {
              path: 'packs',
              children: [
                {path: '', component: PacksComponent},
                {path: 'query/:id/:edit', component: UpdateQueryInPacksComponent},
              ]
          },
          {
              path: 'queries',
              children: [
                {path: '', component: QueriesComponent},
                {path: 'add-query', component: AddQueryComponent},
                {path: ':id/:edit', component: UpdateQueriesInQueriesComponent},
              ]
          },
          {
              path: 'tags',
              children: [
                {path: '', component: TagComponent},
                {path: 'tagged/:value', component: TaggedComponent},
              ]
          },
        ]
    }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class HostsConfigurationRoutingModule { }
