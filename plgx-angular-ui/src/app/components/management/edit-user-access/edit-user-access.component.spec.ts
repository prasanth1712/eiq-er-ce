import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { EditUserAccessComponent } from './edit-user-access.component';

describe('EditUserAccessComponent', () => {
  let component: EditUserAccessComponent;
  let fixture: ComponentFixture<EditUserAccessComponent>;

  beforeEach(waitForAsync(() => {
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
