import { Component, OnInit, ViewChildren, QueryList, ElementRef,} from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { FormControl, FormGroup, FormBuilder, Validators, FormArray } from '@angular/forms';
import { CommonapiService } from '../../../dashboard/_services/commonapi.service';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import swal from 'sweetalert';
import Swal from 'sweetalert2';
import { AuthorizationService } from '../../../dashboard/_services/Authorization.service';
import { Subject } from 'rxjs';
import 'datatables.net';
import { DataTableDirective } from 'angular-datatables';
import { flyInOutRTLAnimation } from '../../../../assets/animations/right-left-animation';
@Component({
  selector: 'app-yara',
  templateUrl: './yara.component.html',
  animations: [flyInOutRTLAnimation],
  styleUrls: ['./yara.component.css']
})
export class YaraComponent implements OnInit {
  yarafile: FormGroup;
  edityarafile: FormGroup;
  yaras:any;
  yara_data:Array<any> = [];
  yara_value:Array<any> = [];
  submitted:any;
  yara:any;
  yara_view:any;
  yaraTitle:any;
  yara_upload:any;
  yara_delete:any;
platform_value:any;
FileSizeError: boolean = false;
maxFileSize: any = 2000000;
platform_group:Array<any> = [];

yaraObj = {};
yaraArray = [];
yaraEditPlatforms: any =[];

enableChild: any = false;
isVisible: any = false;
selectedRow: any;
selectedYara: any;

dtOptions: DataTables.Settings = {};
@ViewChildren(DataTableDirective)
dtElement: DataTableDirective;
dtTrigger: Subject<any> = new Subject();

objectKeys = Object.keys;

editingYara: any = {
  name: '',
  platform: ''
}

platformOptions = [
  { value: 'any', description: 'any' },
  { value: 'windows', description: 'Windows' },
  { value: 'linux', description: 'Linux' },
  { value: 'darwin', description: 'Darwin' }
];
platformSelectControl = new FormControl('windows');


selectedPlatform: string = "any";
role={'adminAccess':this.authorizationService.adminLevelAccess,'userAccess':this.authorizationService.userLevelAccess};
  constructor(
    private httpClient: HttpClient,
    private fb: FormBuilder,
    private commonapi:CommonapiService,
    private router: Router,
    private authorizationService: AuthorizationService,
  ) { }
  @ViewChildren("checkboxes") checkboxes: QueryList<ElementRef>;
  ngOnInit() {
    this.yarafile = this.fb.group({
      yara:'',
      platform_val:this.fb.array([], [Validators.required])
    });
    this.edityarafile = this.fb.group({
      platform_val:this.fb.array([], [Validators.required])
    });
    this.yara=this.yarafile.value.yara
    this.platform_value = 'any';
    this.getyaraData(true);
    if((typeof environment.file_max_size == 'number') && environment.file_max_size> 0 && environment.file_max_size< 1073741824){
      this.maxFileSize = environment.file_max_size
    }
  }
  get f() { return this.yarafile.controls; }

  getyaraData(showAll?){

    this.yara_data = [];
    var temp1 = [];
    this.commonapi.yara_api().subscribe(res => {
      this.yaras = res ;
      let newArray: any = []
      const obj = {}
      var keys = Object.keys(this.yaras.data)
      keys.forEach(element => {
          this.yaras.data[element].forEach(elem => {

             
              if(newArray.indexOf(elem) === -1) {
                newArray.push(elem)
                obj[elem] = []
                obj[elem].push(element)
              }
              else{
                obj[newArray[newArray.indexOf(elem)]].push(element)
              }

          });
      });
      temp1[this.platform_value] = this.yaras.data[this.platform_value];
      Object.keys(temp1).forEach(key => {
        this.yara_data.push({"key":key,"value":temp1[key]});
      });
      if(!showAll){
        this.yara_value = this.yara_data[0].value;

      }
      else if(showAll){
        this.yara_value = newArray
      }
      this.yaraObj = obj
      this.yaraArray = newArray
    });
    

  }
  clearValue:string = '';
  clearInput() {
    this.clearValue = null;
    this.platform_group = [];
    const website: FormArray = this.yarafile.get('platform_val') as FormArray;
    website.clear();
    this.checkboxes.forEach((element) => {
      element.nativeElement.checked = false;
    });
  }
  getByFilterId(platform){
    this.platform_value = platform;
    this.getyaraData();
  }
  getByFilter(event){
    if(event.value == ' ' || event.value == 'any'){
      this.platform_value = 'any'
      this.getyaraData(true);
    }
    else{
      this.platform_value = event.value;
      this.getyaraData();
    }
  }
onFileSelect(event){
  if (event.target.files.length > 0) {
    if(event.target.files[0].size > environment.file_max_size){
      Swal.fire({
        icon: 'warning',
        text: 'Max file size is ' + (this.maxFileSize / 1048576).toFixed(2) + 'MB'
        })
      this.FileSizeError = true
    }
    else{
      this.yara = event.target.files;
      this.FileSizeError = false
    }
  }
}
onSubmit() {
  if (this.yara[0]==null  || this.yara ==''){
    swal(
      "Please select a yara file for upload"
    )
  }
  if(this.yarafile.controls['platform_val'].errors != null){
    if(this.yarafile.controls['platform_val'].errors.required){
      swal(
        "Please select any platform!!"
      )
    }
  }
  this.submitted = true;
    if (this.yarafile.invalid) {
    return;
    }
  this.commonapi.yara_add_api(this.yara, this.platform_group).subscribe(res =>{
    this.yara_upload = res;
    if(this.yara_upload && this.yara_upload.status === 'failure'){
      swal({
        icon: 'warning',
        title: this.yara_upload.status,
        text: this.yara_upload.message,

      })
    }else{
      swal({
        icon: 'success',
        title: this.yara_upload.status,
        text: this.yara_upload.message,
        buttons: [false],
        timer: 2000
      })
      setTimeout(() => {
        this.getyaraData(this.platform_value == 'any');
      },1500);
    }
    this.closeModal('add_yara')
    this.clearInput()
		},
    err => {
      if(err.status == 413)
        Swal.fire({
          icon: 'error',
          text: 'Request entity is too large, please upload file less than ' + (this.maxFileSize / 1048576).toFixed(2) + 'MB'
        })
      else{
        Swal.fire({
          icon: 'error',
          text: err.statusText
        })
      }
    })
}
onSubmitEdit(yarafile) {
  if (yarafile==null  || yarafile==''){
    swal(
      "Please select a yara file for upload"
    )
  }
  this.submitted = true;
    if (this.yarafile.invalid) {
    return;
    }
  this.commonapi.yara_edit_api(yarafile, this.platform_group.toString()).subscribe(res =>{
    this.yara_upload = res;
    if(this.yara_upload && this.yara_upload.status === 'failure'){
      swal({
        icon: 'error',
        title: this.yara_upload.status,
        text: this.yara_upload.message,

      })
    }else{
      swal({
        icon: 'success',
        title: this.yara_upload.status,
        text: this.yara_upload.message,
        buttons: [false],
        timer: 2000
      })
      setTimeout(() => {
        this.getyaraData(this.platform_value == 'any');
      },1500);
    }
    this.closeModal('edit_yara')
    this.clearInput()
	})
}
viewFile(file,$event?){
  if($event?.target?.className?.includes('no-click-event') && $event){
    return ;
  }else{
  var file_type = file;
  this.commonapi.yara_view_api(file_type,this.platform_value).subscribe(res => {
      this.yara_view = res;
      this.yaraTitle = file;
    })
    this.openModal('yara_view')
  }
}
editYara(event){
  this.editingYara.name = event
  this.editingYara.platform = this.findPlatforms(this.editingYara.name)
  this.openModal('edit_yara')
}
checkPlatformExists(platform,array){
  if(array.indexOf(platform) === -1){
    return false;
  }
  else{
    return true;
  }
}
getAllPlatforms(name,platform){
  if(this.yaraObj[name].indexOf(platform) === -1){
    return false;
  }
  else{
    return true;
  }
}
findPlatforms(name){
  return this.yaraObj[name];
}
onItemChange(e){
  const website: FormArray = this.yarafile.get('platform_val') as FormArray;

    if (e.target.checked) {
      website.push(new FormControl(e.target.value));
    } else {
       const index = website.controls.findIndex(x => x.value === e.target.value);
       website.removeAt(index);
    }
    this.platform_group =website.value;
}
deleteFile(event){
    var yara_name = event;
    var platforms: any;
    Swal.fire({
      title: 'Are you sure?',
      text: "You won't be able to revert this!",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#518c24',
      cancelButtonColor: '#d33',
      confirmButtonText: "Yes, delete it!"
    }).then((result) => {
      if (result.value) {
          platforms = this.findPlatforms(yara_name).toString()
        this.commonapi.yara_delete_api(yara_name, platforms).subscribe(res => {
          this.yara_delete = res;
          swal({
            icon: this.yara_delete.status == 'failure' ? 'warning' : this.yara_delete.status,
            title: this.yara_delete.status,
            text: this.yara_delete.message,
            buttons: [false],
            timer: 2000
          })
          setTimeout(() => {
            this.getyaraData(this.platform_value == 'any')
          }, 2100);

        })
      }
})
}
closeModal(modalId){
  ($('#' + modalId) as any).modal('hide')
}
openModal(modalId){
  ($('#' + modalId) as any).modal('show')
}
async toggleShowDiv(yaraData) {
  this.selectedYara = yaraData
  this.enableChild = true;
  this.isVisible = true;
}
toggleHideDiv(){
  this.enableChild = false;
  this.isVisible = false;
}
}
