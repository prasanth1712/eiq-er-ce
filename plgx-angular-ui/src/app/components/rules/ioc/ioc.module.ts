import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { IocRoutingModule } from './ioc-routing.module';
import { IocComponent } from './ioc.component';
import { GlobalModule } from '../../global/global.module';
import { NgJsonEditorModule } from 'ang-jsoneditor';

import { SharedModule } from "../../shared/shared.module";


@NgModule({
  declarations: [IocComponent],
  imports: [
    CommonModule,
    IocRoutingModule,
    GlobalModule,
    NgJsonEditorModule,
    SharedModule
  ]
})
export class IocModule { }
