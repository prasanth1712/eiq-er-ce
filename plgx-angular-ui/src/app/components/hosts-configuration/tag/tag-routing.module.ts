import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { TagComponent } from './tag.component';
import { TaggedComponent } from './tagged/tagged.component';


const routes: Routes = [
  {
    path: '',
    component: TagComponent, 
  },
  {
    path: '',
    children: [{
      path:'tagged/:value',component: TaggedComponent,
    }]
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class TagRoutingModule { }
