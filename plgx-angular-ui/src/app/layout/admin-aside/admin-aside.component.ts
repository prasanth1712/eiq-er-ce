import { Component, OnInit,AfterViewInit } from '@angular/core';
import { Router, NavigationEnd,ActivatedRoute } from '@angular/router';
import { Title } from '@angular/platform-browser';
// import { AuthenticationService } from '../../dashboard/_services/authentication.service';
import { User } from '../../dashboard/_models/user';
import { ToastrService } from 'ngx-toastr';
import {Renderer2} from '@angular/core';
import { filter } from 'rxjs/operators';
import { CommonVariableService } from '../../dashboard/_services/commonvariable.service';
import { PlatformLocation } from '@angular/common';
import {CommonapiService} from '../../dashboard/_services/commonapi.service';
import { AuthorizationService } from '../../dashboard/_services/Authorization.service';
import { AlertService } from '../../dashboard/_services/alert.service';
import { AlertsComponent } from '../../widgets/alerts/alerts.component';

@Component({
    selector: 'app-admin-aside',
    templateUrl: './admin-aside.component.html',
    styleUrls: ['./admin-aside.component.css']
})
export class AdminAsideComponent implements OnInit,AfterViewInit {
    // currentUser: User;
    alertNavData:any = [];
    default_menu_name:any;
    id_for_links:any;
    Version=this.commonvariable.Version;
    ProductName=this.commonvariable.ProductName
    MenuName:any;
    isAuthorized:Boolean=false
    currentUser: any;
    hasAcess=this.AuthorizationService.hasAccess()
    constructor(
        private router: Router,
        // private authenticationService: AuthenticationService,
        private toastr:ToastrService,
        private titleService: Title,
        private renderer: Renderer2,
        private commonvariable: CommonVariableService,
        location: PlatformLocation,
        private commonapi: CommonapiService,
        private _Activatedroute: ActivatedRoute,
        private AuthorizationService: AuthorizationService, private alertService: AlertService, private AlertsComponent: AlertsComponent,
    ) {
        // this.authenticationService.currentUser.subscribe(x => this.currentUser = x['roles'][0]);
        this.router.events.pipe(
            filter(event => event instanceof NavigationEnd)
          ).subscribe((event: NavigationEnd) => {
            if(event.url.includes('live-query')){
                this.id_for_links = 'live-queries';
            }
          });
          location.onPopState(() => {
            this.router.events.pipe(
                filter(event => event instanceof NavigationEnd)
              ).subscribe((event: NavigationEnd) => {
                  if(event.url.includes('live-query')){
                      this.id_for_links = 'live-queries';
                  }else{
                    this.id_for_links = 'id_for_links';
                  }
              });
          });
         //  this.router.routeReuseStrategy.shouldReuseRoute = function() {
         //     return false;
         // };
    }
    ngOnInit(){
      this._Activatedroute.params.subscribe(params => {
        var UrlPath = this._Activatedroute.snapshot['_routerState'].url
        var MeueUrl = UrlPath.split("/");
        this.MenuName = MeueUrl[1];
        this.MenuName = this.capitalizeFirstLetter(this.MenuName);
      });
        if(this.MenuName == 'Settings'){
          this.MenuName = 'Management'
        }
        else if(this.MenuName == 'Hostconfiguration'){
          this.MenuName = 'HostConfiguration'
        }
        this.default_menu_name = localStorage.getItem('menu_name');
        var str = window.location.href;
        var page_name = str.substr(str.lastIndexOf('/') + 1);
        if(page_name == "dashboard" || page_name == "manage"){
            this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Dashboard");
            this.MenuName = 'Dashboard';
        }
        else if(page_name == "response-action" || this.MenuName == "response-action" || this.MenuName == "Response-action"){
            this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Response action" );
            this.MenuName = 'Action';
        }
        else if(page_name == "live-query"){
          this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+"Live query" );
           this.MenuName = 'live-queries';
        }
        else{
            this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+ page_name );
        }
        if(this.MenuName != null && typeof this.MenuName!= undefined){
          document.getElementById(this.MenuName).classList.add('kt-menu__item--active');
        }
        else{
          document.getElementById('Dashboard').classList.add('kt-menu__item--active');
        }
        this.renderExternalScript('../../../assets/demo/default/base/scripts.bundle.js').onload = () => {
       // console.log('Google API Script loaded');
      // do something with this library
  }
    }
    ngAfterViewInit(): void {
      var str = window.location.href;
      var page_name = window.location.href.substr(window.location.href.lastIndexOf('/') + 1);

      if(this.MenuName == 'Management' || this.MenuName == 'HostConfiguration' || this.MenuName == 'Rules'){
        document.getElementsByClassName('submenu-id-page_'+page_name)[0].classList.add('kt-aside-submenu--active');
      }
    }
   capitalizeFirstLetter(string) {
     return string.charAt(0).toUpperCase() + string.slice(1);
   }

    action(event): void {
        event.stopPropagation();
    }


    // this function removed all localStorage key value data and redirect to login page
    logout() {
      this.commonapi.logout().subscribe(res => {
        this.toastr.success('You have been signed out.',"",{
          positionClass:'toast-bottom-left',
          messageClass:'toast-grey'
        });
      },
      err=>{
        this.toastr.error(err['message'],"",{
          positionClass:'toast-bottom-left'
        });
      });

      localStorage.removeItem('reset_password');
      localStorage.removeItem('roles');
      localStorage.removeItem('all_roles');
      localStorage.removeItem('token');
      localStorage.removeItem('menu_name');
      this.router.navigate(['/authentication/login']);

    }
    OnNavChange(event, id, active, rel) {
      var myDiv = document.getElementById('kt_aside_menu');
      myDiv.scrollTop = 0;
      console.log(event, id, active, rel)
        this.id_for_links=id;
        localStorage.setItem("menu_name",id);
        this.router.events.pipe(
            filter(event => event instanceof NavigationEnd)
          ).subscribe((event: NavigationEnd) => {
            if(event.url.includes('live-query')){
                this.id_for_links = 'live-queries';
            }
          });
         
        if(id != 'live-queries' && id != 'Action')
        {
          this.titleService.setTitle(this.commonvariable.APP_NAME+" - "+ id.replace('-', ' ') );
        }

        var elems = document.querySelectorAll("." + active);
        [].forEach.call(elems, function (el) { el.classList.remove(active); });
        event.target.parentElement.parentElement.classList.remove(rel);
        document.getElementById(id).classList.add(active);

        if(id !='Management'){
          //collapse Management sub page while click other page
          var div = document.getElementById("submenu");
      	  div.classList.remove("show");
        }
        if(id !='Rules'){
          //collapse Management sub page while click other page
          var div = document.getElementById("Rulessubmenu");
      	  div.classList.remove("show");
        }
        if(id !='HostConfiguration'){
          //collapse Management sub page while click other page
          var div = document.getElementById("Hostconfigsubmenu");
      	  div.classList.remove("show");
        }
        if(id !='HostConfiguration' &&  id !='Rules' && id !='Management'){
          this.removeSubmenuActive();
        }
    }


    OnSubNavChange(event,parentId, id, active, rel) {
     event.stopPropagation();
     this.removeSubmenuActive()
     var elems = document.querySelectorAll("." + active);
     [].forEach.call(elems, function (el) { el?.classList?.remove(active); });
     event.target.parentElement.parentElement?.classList?.remove(rel);
     document.getElementById(id).classList?.add(active);
     document.getElementById(id).classList?.remove('kt-menu__submenuitem--focus');
     document.getElementById(parentId).classList?.add('kt-menu__submenuitem--focus');

     var elems = document.querySelectorAll(".kt-menu__item--active");
     [].forEach.call(elems, function (el) { el?.classList?.remove("kt-menu__item--active"); });
    }

    removeSubmenuActive(){
      var elems = document.querySelectorAll(".kt-aside-submenu--active");
      [].forEach.call(elems, function (el) { el?.classList?.remove("kt-aside-submenu--active"); });

      var focusSubmenu= document.querySelectorAll(".kt-menu__submenuitem--focus");
      [].forEach.call(focusSubmenu, function (el) { el?.classList?.remove("kt-menu__submenuitem--focus"); });

      var activeSubmenu = document.querySelectorAll(".kt-menu__submenuitem--active");
      [].forEach.call(activeSubmenu, function (el) { el?.classList?.remove("kt-menu__submenuitem--active"); });
    }

    collapsemanagementmenu(){
      var divManage = document.getElementById("submenu");
      divManage.classList.remove("show");
      var divRules = document.getElementById("Rulessubmenu");
      divRules.classList.remove("show");
      var divConfg = document.getElementById("Hostconfigsubmenu");
      divConfg.classList.remove("show");
    }
    resizeAlertGraph(){
      if(this.router?.url?.includes('alerts')){
        this.alertService.resData.subscribe(data => (this.alertNavData= data));
        this.AlertsComponent.onResieNavMenu(this.alertNavData);
      }
    }


    public setTitle( newTitle: string) {

      }
      renderExternalScript(src: string): HTMLScriptElement {
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = src;
        script.async = true;
        script.defer = true;
        this.renderer.appendChild(document.body, script);
        return script;
      }

}
var KTAppOptions = {
    "colors": {
        "state": {
            "brand": "#5d78ff",
            "metal": "#c4c5d6",
            "light": "#ffffff",
            "accent": "#00c5dc",
            "primary": "#5867dd",
            "success": "#34bfa3",
            "info": "#36a3f7",
            "warning": "#ffb822",
            "danger": "#fd3995",
            "focus": "#9816f4"
        },
        "base": {
            "label": [
                "#c5cbe3",
                "#a1a8c3",
                "#3d4465",
                "#3e4466"
            ],
            "shape": [
                "#f0f3ff",
                "#d9dffa",
                "#afb4d4",
                "#646c9a"
            ]
        }
    }
};
