import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BibliographyInfoComponent } from './bibliography-info.component';

describe('BibliographyInfoComponent', () => {
  let component: BibliographyInfoComponent;
  let fixture: ComponentFixture<BibliographyInfoComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ BibliographyInfoComponent ],
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(BibliographyInfoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
