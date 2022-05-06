import { Component, OnInit, ViewChildren, QueryList, ElementRef } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { FormControl, FormGroup, FormBuilder, Validators, FormArray } from '@angular/forms';
import { CommonapiService } from '../../dashboard/_services/commonapi.service';
import { HttpClient } from '@angular/common/http';
import swal from 'sweetalert';
import Swal from 'sweetalert2';
import { AuthorizationService } from '../../dashboard/_services/Authorization.service';
@Component({
  selector: 'app-yara',
  templateUrl: './yara.component.html',
  styleUrls: ['./yara.component.css']
})
export class YaraComponent implements OnInit {
  yarafile: FormGroup;
  yaras:any;
  yara_data:Array<any> = [];
  yara_value:Array<any> = [];
  submitted:any;
  yara:any;
  yara_view:any;
  yara_title:any;
  yara_upload:any;
  yara_delete:any;
platform_value:any;
platform_group:Array<any> = [];
objectKeys = Object.keys;
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
    this.yara=this.yarafile.value.yara
    this.platform_value = 'windows';
    this.getyaraData();
  }
  get f() { return this.yarafile.controls; }

  getyaraData(){
    this.yara_data = [];
    var temp1 = [];
    this.commonapi.yara_api().subscribe(res => {
      this.yaras = res ;
      temp1[this.platform_value] = this.yaras.data[this.platform_value];
      Object.keys(temp1).forEach(key => {
        this.yara_data.push({"key":key,"value":temp1[key]});
      });
      this.yara_value = this.yara_data[0].value;
      console.log(this.yara_data.length);
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
onFileSelect(event){
  if (event.target.files.length > 0) {
    this.yara = event.target.files;
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
    // this.platform_value = this.yarafile.value.platform_value;
  this.commonapi.yara_add_api(this.yara, this.platform_group).subscribe(res =>{
    this.yara_upload = res;
    // console.log(res);
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
        this.getyaraData();
        // $('.nav-link').removeClass("active");
        // $('#windows').addClass("active");
        // this.ngOnInit()
      },1500);
    }    
    this.clearInput()
		})
}
viewFile(event){
  var event_type = event;
  this.commonapi.yara_view_api(event_type,this.platform_value).subscribe(res => {
      this.yara_view = res;
      this.yara_title = event;
    })
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
  //this.getyaraData();
}
deleteFile(event){
    console.log(event);
    var yara_name = event;
  //   swal({
  //   title: 'Are you sure?',
  //   text: "You won't be able to revert this!",
  //   icon: 'warning',
  //   buttons: ["cancel", "Yes, delete it!"],
  //   dangerMode: true,
  //   closeOnClickOutside: false

  // }).then((willDelete) => {
  // if (willDelete) {
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
    this.commonapi.yara_delete_api(yara_name,this.platform_value).subscribe(res=>{
      this.yara_delete = res;
      swal({
        icon: 'success',
        title: 'Deleted!',
        text: '',
        buttons: [false],
        timer: 2000
        })
    setTimeout(() => {
      this.getyaraData()
    },2100);
     
  })
  }
})
}
}

