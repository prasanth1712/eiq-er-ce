import { Injectable, OnInit } from '@angular/core';
@Injectable({
  providedIn: 'root'
})
export class AuthorizationService  {
adminLevelAccess=['admin']
userLevelAccess=['analyst']
    hasAccess(){
      if(['admin'].includes(localStorage.getItem('roles'))){
        return true
      }else{
        return false
      }
    }
      hasRoles(roles:string[]):Boolean {
        for(const onerole in roles){
        if((localStorage.getItem('roles')).includes(roles[onerole])){
          return true
        }  
      }
    } 
}
