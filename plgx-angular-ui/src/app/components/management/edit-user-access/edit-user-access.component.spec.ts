import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { EditUserAccessComponent } from './edit-user-access.component';

describe('EditUserAccessComponent', () => {
  let component: EditUserAccessComponent;
  let fixture: ComponentFixture<EditUserAccessComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ EditUserAccessComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(EditUserAccessComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
