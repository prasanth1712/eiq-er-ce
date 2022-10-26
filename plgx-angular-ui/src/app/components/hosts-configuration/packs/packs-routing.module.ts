import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { PacksComponent } from './packs.component';
import { UpdateQueryInPacksComponent } from './update-query-in-packs/update-query-in-packs.component';


const routes: Routes = [
  {
    path: '',
    component: PacksComponent,
  },
  {
    path: '',
    children: [{
      path: 'query/:id/:edit', component: UpdateQueryInPacksComponent,
    }]
  },
  {
    path: ':packname',
    component: PacksComponent,
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PacksRoutingModule { }
