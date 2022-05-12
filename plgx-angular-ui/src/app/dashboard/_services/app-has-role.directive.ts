import { Directive ,Input,TemplateRef,ViewContainerRef,OnInit,ElementRef} from '@angular/core';
import { AuthorizationService } from './Authorization.service';

@Directive({
  selector: '[AppHasRole]'
})
export class AppHasRoleDirective implements OnInit {

  Permissions=[]
@Input('AppHasRole')roles:string[];
  constructor(private authService: AuthorizationService,private templateref:TemplateRef<any>,private viewcontainer:ViewContainerRef ,private el:ElementRef) { 
   
  } 
  ngOnInit(){  
      if(this.authService.hasRoles(this.roles)){
        this.viewcontainer.createEmbeddedView(this.templateref)
      }else{
        this.viewcontainer.clear()
      }       
  }
}

