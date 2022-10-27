import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { QueriesComponent } from './queries.component';
import { AddQueryComponent } from './add-query/add-query.component';
import { UpdateQueriesInQueriesComponent } from './update-queries-in-queries/update-queries-in-queries.component';


const routes: Routes = [
  {
    path: '',
    component: QueriesComponent, 
  },
  {
    path: '',
    children: [{
      path: 'add-query', component: AddQueryComponent,
    }]
  },
  {
    path: '',
    children: [{
      path: ':id/:edit', component: UpdateQueriesInQueriesComponent,
    }]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class QueriesRoutingModule { }
