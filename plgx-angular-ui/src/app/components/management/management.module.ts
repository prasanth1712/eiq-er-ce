import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ManagementComponent } from './management.component';
import { ConfigureEmailComponent } from './configure-email/configure-email.component';
import { IntelKeysComponent } from './intel-keys/intel-keys.component';
import { GlobalModule } from '../../global/global.module';
import { ManagementRoutingModule} from '../management/management-routing';
import { ResolvedAlertsComponent } from './resolved-alerts/resolved-alerts.component';
// import { ConfigurationSettingsComponent } from './configuration-settings/configuration-settings.component';
import { AntivirusEnginesComponent } from './antivirus-engines/antivirus-engines.component';
import { HostDisableComponent } from './host-disable/host-disable.component';
import { UserAdministrationComponent } from './user-administration/user-administration.component'
import { DataTablesModule } from 'angular-datatables';
import { NgJsonEditorModule } from 'ang-jsoneditor';
import { TagInputModule } from 'ngx-chips';
import { EditUserAccessComponent } from './edit-user-access/edit-user-access.component';
import { AngularMultiSelectModule } from 'angular2-multiselect-dropdown';
import {ChangeUserPasswordModule} from '../change-user-password/change-user-password.module';
import {NgbDatepickerModule} from '@ng-bootstrap/ng-bootstrap';
import { TroubleshootingComponent } from './troubleshooting/troubleshooting.component';
import { AlertConfigurationComponent } from './alert-configuration/alert-configuration.component';
import { DataPurgeComponent } from './data-purge/data-purge.component';
import { SsoConfigurationComponent } from './sso-configuration/sso-configuration.component';
@NgModule({
  declarations: [
    ManagementComponent,
    ConfigureEmailComponent,
    IntelKeysComponent,
    ResolvedAlertsComponent,
    // ConfigurationSettingsComponent,
    AntivirusEnginesComponent,
    HostDisableComponent,
    UserAdministrationComponent,
    EditUserAccessComponent,
    TroubleshootingComponent,
    AlertConfigurationComponent,
    DataPurgeComponent,
    SsoConfigurationComponent
  ],
  imports: [
     CommonModule,
     ManagementRoutingModule,
     FormsModule,
     ReactiveFormsModule,
     CommonModule,
     GlobalModule,
     RouterModule,
     DataTablesModule,
     NgJsonEditorModule,
     TagInputModule,
     AngularMultiSelectModule,
     ChangeUserPasswordModule,
     NgbDatepickerModule
  ],
})
export class ManagementModule { }
