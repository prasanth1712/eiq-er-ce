import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { YaraRoutingModule } from './yara-routing.module';
import { YaraComponent } from './yara.component';
import { GlobalModule } from '../../global/global.module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { SharedModule } from 'src/app/shared/shared.module';


@NgModule({
  declarations: [YaraComponent],
  imports: [
    CommonModule,
    YaraRoutingModule,
    GlobalModule,
    FormsModule,
    ReactiveFormsModule,
    SharedModule
  ]
})
export class YaraModule { }
