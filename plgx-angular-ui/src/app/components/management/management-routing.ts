import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';;
import { ConfigureEmailComponent } from './configure-email/configure-email.component';
import { IntelKeysComponent } from './intel-keys/intel-keys.component';
import { ManagementComponent } from './management.component';
// import { ConfigurationSettingsComponent } from './configuration-settings/configuration-settings.component';
import { AntivirusEnginesComponent } from './antivirus-engines/antivirus-engines.component';
import { UserAdministrationComponent } from './user-administration/user-administration.component';
import { EditUserAccessComponent } from './edit-user-access/edit-user-access.component';
import { ChangeUserPasswordComponent } from './../change-user-password/change-user-password.component';
import { TroubleshootingComponent } from './troubleshooting/troubleshooting.component';
import { AlertConfigurationComponent } from './alert-configuration/alert-configuration.component';
import { SsoConfigurationComponent } from './sso-configuration/sso-configuration.component'
import { DataPurgeComponent } from './data-purge/data-purge.component';
const routes: Routes = [
    {
        path: '',
        children: [
            // { path: '', redirectTo: 'login', pathMatch: 'full' },
            {
                path: 'change-password',
                component: ChangeUserPasswordComponent
            },
            {
                path: 'email',
                component: ConfigureEmailComponent
            },
            {
                path: 'threat-intel-keys',
                component: IntelKeysComponent
            },
            // {
            //     path: 'configuration',
            //     component: ConfigurationSettingsComponent
            // },
            {
                path: 'alert-settings',
                component: AlertConfigurationComponent
            },
            {
                path: 'troubleshooting',
                component: TroubleshootingComponent
            },
            {
                path: 'sso-settings',
                component: SsoConfigurationComponent
            },
            {
                path: 'data-purge',
                component: DataPurgeComponent
            },
            {
                path: 'vt-settings',
                component: AntivirusEnginesComponent
            },
              {
                path: 'user-management',
                component: UserAdministrationComponent,
              },
              {
                path: 'edit/:id',
                component: EditUserAccessComponent,
              },
        ]
    }


]

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class ManagementRoutingModule { }
