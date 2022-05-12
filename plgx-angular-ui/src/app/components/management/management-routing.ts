import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';;
import { ConfigureEmailComponent } from './configure-email/configure-email.component';
import { IntelKeysComponent } from './intel-keys/intel-keys.component';
import { ManagementComponent } from './management.component';
import { ResolvedAlertsComponent } from './resolved-alerts/resolved-alerts.component';
// import { ConfigurationSettingsComponent } from './configuration-settings/configuration-settings.component';
import { AntivirusEnginesComponent } from './antivirus-engines/antivirus-engines.component';
import { HostDisableComponent } from './host-disable/host-disable.component';
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
                path: 'configure-email',
                component: ConfigureEmailComponent
            },
            {
                path: 'threat-intel-keys',
                component: IntelKeysComponent
            },
            {
                path: 'resolved-alerts',
                component: ResolvedAlertsComponent
            },
            // {
            //     path: 'configuration',
            //     component: ConfigurationSettingsComponent
            // },
            {
                path: 'alert-configuration',
                component: AlertConfigurationComponent
            },
            {
                path: 'troubleshooting',
                component: TroubleshootingComponent
            },
            {
                path: 'sso-configuration',
                component: SsoConfigurationComponent
            },
            {
                path: 'data-purge',
                component: DataPurgeComponent
            },
            {
                path: 'vt-configuration',
                component: AntivirusEnginesComponent
            },
            {
                path: 'removed-hosts',
                component: HostDisableComponent,
              },
              {
                path: 'UserAdministration',
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
