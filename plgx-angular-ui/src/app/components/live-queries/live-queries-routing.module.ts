import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { LiveQueriesComponent } from './live-queries.component';


const routes: Routes = [ {
  path: '',
  component: LiveQueriesComponent, 
},
{
  path: '',
  children: [{
    path:'live-query/:id',component: LiveQueriesComponent,
  },
  {
    path:':id', component:LiveQueriesComponent
  },
]
},

];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class LiveQueriesRoutingModule { }
