import { Component, OnInit,ViewChild, AfterViewInit } from '@angular/core';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { JsonEditorComponent, JsonEditorOptions } from 'ang-jsoneditor';
import { FormControl, FormGroup, FormBuilder, Validators, FormArray } from '@angular/forms';
import Swal from 'sweetalert2';
import { ToastrService } from 'ngx-toastr';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';
import { environment } from '../../../../environments/environment'

@Component({
  selector: 'app-config',
  templateUrl: './config.component.html',
  styleUrls: ['./config.component.css', './config.component.scss']
})
export class ConfigComponent implements OnInit{
 @ViewChild(JsonEditorComponent, { static: true }) editor: JsonEditorComponent;
 public editorOptions: JsonEditorOptions;
 options = new JsonEditorOptions();
 custom_config_Form: FormGroup;
 submitted = false;
 Platform_name:any;
 config_name='Default'
 custom_config_list=[]
 selectedItem:any;
 public config: any;
 public config_data: any = [];
 public filters={};
 public dict_data_to_api:any={};
 toggle:boolean=false;
 fieldTextType: boolean;
 confirmationForm:FormGroup;
 maxInputCharacters = (environment?.input_max_size)? environment.input_max_size : 256;

 //config_dropdown
 config_list_dropdown = [];
 config_list_selectedItems = [];
 config_list_dropdownSettings = {};

  EditHostname='';
  EditOS=''
  EditDescription='';
  validationMessage=''
  operation:any;
  hasAcess=this.authorizationService.hasAccess()
  role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess}
constructor(
  private fb: FormBuilder,
    private commonapi: CommonapiService,
    private toaster: ToastrService,
    private authorizationService: AuthorizationService,
  ) {
  this.options.onChange = () =>this.dict_data_to_api['filters']=this.editor.get();
  }
showDataAsPerPlatformSelection(platform,configData){
  this.Platform_name=platform
  this.custom_config_list=Object.keys(configData)
  this.get_details_of_custom_config(platform,this.custom_config_list[0])
  this.config_list_selectedItems=[]
}
ngOnInit() {
  if(this.authorizationService.hasAccess()){
    this.options.modes = ['code', 'text', 'view'];
    this.options.mode = 'code';
  } else{
     this.options.mode = 'code';
  }
  this.toggle=false;
    this.commonapi.configs_api().subscribe((res: any) => {
        this.config = res;
        this.editorOptions = new JsonEditorOptions();
        this.custom_config_list=Object.keys(this.config.data.windows)
        $('.config_body_loader').hide();
        $('.config_body').show();
        this.Platform_name='windows'
        this.toggle=true;
        let result = this.getDefaultConfig(res.data.windows,this.custom_config_list)
        this.custom_config_list = result.keys
        this.config.data['windows'] = result.array
        this.get_details_of_custom_config(this.Platform_name,this.custom_config_list[0])
  });
  this.custom_config_Form = this.fb.group({
    Config_Name: ['',[Validators.required, Validators.maxLength(this.maxInputCharacters)]],
    config_list:['',Validators.required],
    OperatorlistForHostname:[''],
    OperatorlistForOs:[''],
    host_Name: [''],
    Os_Name: ['' ],
    Description:['',Validators.required]
  });

  this.config_list_dropdownSettings = {
    singleSelection: true,
    text: "Select Config",
    selectAllText: 'Select All',
    unSelectAllText: 'Unselect All',
    badgeShowLimit: 1,
    enableSearchFilter: true,
    filterSelectAllText: "Select filtered result",
    classes: "config_list custom-class"
  };
}
get f() { return this.custom_config_Form.controls; }
get p() { return this.confirmationForm.controls; }

uploadDefaultData(){
  this.dict_data_to_api['platform']=this.Platform_name;
  this.dict_data_to_api['queries']=this.config.data[this.Platform_name][this.config_name].queries
  this.dict_data_to_api['filters']=this.config.data[this.Platform_name][this.config_name].filters
}
get_config_api(type){
  this.commonapi.configs_api().subscribe((res: any) => {
     if(res["status"]=="success"){
          this.config = res;
          this.assign_data(type)
     }else{
      this.get_swal_failure_message(res["message"])
     }
  })
}
get_details_of_custom_config(platform,configname){
  this.selectedItem=configname
  this.config_name=configname
  this.config_data=this.config.data[platform][configname]['queries']
  this.filters=this.config.data[platform][configname]['filters']
  if(this.config.data[platform][configname]['conditions']!=null){
          if(this.config.data[platform][configname]['conditions']['hostname']){
            this.EditHostname=this.config.data[platform][configname]['conditions']['hostname'].value;
          }else{
            this.EditHostname=''
          }
          if(this.config.data[platform][configname]['conditions']['os_name']){
            this.EditOS=this.config.data[platform][configname]['conditions']['os_name'].value
          }else{
            this.EditOS=''
          }
  }
  this.EditDescription=this.config.data[platform][configname].description;
  this.uploadDefaultData()
}

//start create_custom_config
create_custom_config(){
  this.validationMessage=''
  const body = document.querySelector("body");
  body.style.overflow = "hidden";
  let modal = document.getElementById("create_custom_config_Modal");
  modal.style.display = "block";
  modal.style.overflow = "auto";
  this.config_list_dropdown=[]
  Object.keys(this.config.data[this.Platform_name]).forEach(key => {
    this.config_list_dropdown.push({id: this.config.data[this.Platform_name][key]["id"], itemName: key});

  });
}
onSubmit_add_custom_config_Form() {
  this.submitted = true;
    if (this.custom_config_Form.invalid) {
        return;
    }
    if( this.custom_config_list.includes(this.f.Config_Name.value)){
      this.validationMessage="Config name already exists"

    }else{
      var payload={}
      payload["conditions"]={}
      payload["queries"]=this.config.data[this.Platform_name][this.config_list_selectedItems[0]['itemName']].queries
      payload["filters"]=this.config.data[this.Platform_name][this.config_list_selectedItems[0]['itemName']].filters
      payload["name"]=this.f.Config_Name.value
      payload["platform"]=this.Platform_name
      payload["description"]=this.f.Description.value
      if(this.f.host_Name.value!='' && this.f.host_Name.value!=null){
        payload["conditions"]["hostname"]={}
        payload['conditions']['hostname']['value']=this.f.host_Name.value
      }
      if(this.f.Os_Name.value!='' && this.f.Os_Name.value!=null){
      payload["conditions"]["os_name"]={}
      payload['conditions']['os_name']['value']=this.f.Os_Name.value
      }

    this.commonapi.add_custom_config(payload).subscribe(res => {
        if(res["status"]=="success"){
          this.get_config_api("add")
          this.get_swal_success_message(res["message"])
        }else{
          this.get_swal_failure_message(res["message"])
        }
    })
    this.close_add_custom_modal()
  }
}
assign_data(type) {
  switch(type) {
    case 'add':
      this.custom_config_list=Object.keys(this.config.data[this.Platform_name])
      break;
    case 'update':
      this.config_data=this.config.data[this.Platform_name][this.config_name]['queries']
      this.filters=this.config.data[this.Platform_name][this.config_name]['filters']
      this.uploadDefaultData()
      break;
    case 'delete':
      this.custom_config_list=Object.keys(this.config.data[this.Platform_name])
      this.get_details_of_custom_config(this.Platform_name,this.custom_config_list[0])
      break;
    default:
  }
}

close_add_custom_modal() {
  this.submitted = false;
  this.custom_config_Form.reset()
  const body = document.querySelector("body");
  body.style.overflow = "auto";
  let modal = document.getElementById("create_custom_config_Modal");
  modal.style.display = "none";
  }
//ENd create_custom_config

public setTreeMode() {
   this.editor.setMode('code');
 }


get_changed_data(changed_data){
    this.dict_data_to_api['queries']=changed_data;
}
//start onSubmit update
  OnSubmitUpdate(){
    if(!this.editor.isValidJson()){
      Swal.fire({icon: "warning",title:"Please upload valid JSON"})
      return;
    }
    for (const i in this.dict_data_to_api['queries']){
      if(this.dict_data_to_api['queries'][i].interval<1 || this.dict_data_to_api['queries'][i].interval>604800){
        Swal.fire({title:"Please check interval range"})
        return
      }
    }
    if(this.dict_data_to_api['filters'].hasOwnProperty('options')){
      if((this.dict_data_to_api['filters']['options'].hasOwnProperty('custom_plgx_MemoryLimitLow') &&  (this.dict_data_to_api['filters']['options']['custom_plgx_MemoryLimitLow']<50)) || (this.dict_data_to_api['filters']['options'].hasOwnProperty('custom_plgx_MemoryLimitHigh') &&  (this.dict_data_to_api['filters']['options']['custom_plgx_MemoryLimitHigh']>350))){
        var ErrorMessage="custom_plgx_MemoryLimitLow should be greater than 50\n" +
                "custom_plgx_MemoryLimitHigh should be less than 350\n";
        Swal.fire({
          icon:'warning',
          html:  '<b>'+'MemoryLimit should be:'+'</b>'+'<pre>'+ ErrorMessage + '</pre>',
          customClass: {
            popup: 'format-pre'
          }
        });
        return
      }
    }
    Swal.fire({
     title: 'Are you sure want to update?',
     icon: 'warning',
     showCancelButton: true,
     confirmButtonColor: '#518c24',
     cancelButtonColor: '#d33',
     confirmButtonText: 'Yes, Update!'
   }).then((result) => {
      if (result.value) {
        this.updateConfig()
      }
   })
  }
  toggleFieldTextType() {
    this.fieldTextType = !this.fieldTextType;
  }
  updateConfig(){
    Swal.fire({
      title: 'Please Wait..',
      onBeforeOpen: () => {
        Swal.showLoading()
      }
    })
  this.dict_data_to_api["conditions"]={}
  if(this.EditOS!='' || this.EditHostname!='' ){
    this.dict_data_to_api["conditions"]={"hostname":{},"os_name":{}}
    this.dict_data_to_api['conditions']['os_name']['value']=this.EditOS
    this.dict_data_to_api['conditions']['hostname']['value']=this.EditHostname
  }
  if(this.EditDescription==""){
    this.get_swal_failure_message('Please provide description')
  }else{
  this.dict_data_to_api['description']=this.EditDescription
      this.commonapi.config_upload(this.config.data[this.Platform_name][this.config_name].id,this.dict_data_to_api).subscribe(res=>{
        Swal.close()
      if(res["status"]=="success"){
        this.get_config_api('update')
        this.get_swal_success_message(res["message"])
      }
      else{
        this.get_swal_failure_message(res["message"])
      }
      },(error) => {
        Swal.close()
      })
    }
  }

  OnSubmitDelete(){
    Swal.fire({
     title: 'Are you sure want to Delete?',
     icon: 'warning',
     showCancelButton: true,
     confirmButtonColor: '#518c24',
     cancelButtonColor: '#d33',
     confirmButtonText: 'Yes, Delete!'
   }).then((result) => {
      if (result.value) {
        this.deleteConfig()
      }
   })
  }

  //start delete config
  deleteConfig(){
    this.commonapi.delete_config(this.config.data[this.Platform_name][this.config_name].id).subscribe(res=>{
      if(res["status"]=="success"){
        this.get_config_api("delete")
        this.get_swal_success_message(res["message"])
      }else{
          this.get_swal_failure_message(res["message"])
      }
    })
  }
  //End delete config
  get_swal_success_message(message){
    Swal.fire({
      icon: 'success',
      text: message
      })
    }
  get_swal_failure_message(message){
    Swal.fire({
      icon: 'warning',
      text:message
      })
  }
  getDefaultConfig(configArray,keysArray){
    let tempobj: any;
    let tempkey: any;
    keysArray.forEach(element => {
      if(configArray[element].is_default){
        tempobj = configArray[element]
        tempkey = element
        delete configArray[element];
        return;
      }
    });
    let tempassign = {}
    tempassign[tempkey] = tempobj
    configArray = Object.assign(tempassign,configArray)
    return {keys:Object.keys(configArray), array: configArray}
  }

  // Start config_list
  onItemSelect_config(item: any) {
    console.log(item);
  }
  OnItemDeSelect_config(item: any) {
    console.log(item);
  }
  onDeSelectAll_config(items: any) {
    this.config_list_selectedItems=[]
  }
  closeModal(modalId){
    let modal = document.getElementById(modalId);
    modal.style.display = "none";
    $('.modal-backdrop').remove();
  }
  openModal(modalId){
    ($('#' + modalId) as any).modal('show')
  }
  // End config_list
}
