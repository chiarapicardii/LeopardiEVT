import { Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { EvtIconInfo } from '../../ui-components/icon/icon.component';
import { EVTStatusService } from 'src/app/services/evt-status.service';
import { distinctUntilChanged, Subscription } from 'rxjs';
import { AppConfig } from 'src/app/app.config';
import { ChangeLayerData } from 'src/app/models/evt-models';

@Component({
  selector: 'evt-change-layer-selector',
  templateUrl: './change-layer-selector.component.html',
  styleUrls: ['./change-layer-selector.component.scss'],
})
export class ChangeLayerSelectorComponent implements OnDestroy, OnInit {

  private subscription: Subscription;

  public selectedLayer: string;
  public changeLayers: Array<{id: string; value: string}>;

  @Input() set selLayer(l: string) {
    if (l) {
      this.selectedLayer = l;
      this.layerChange.emit(l);
    }
  }

  get selLayer() { return this.selectedLayer; }

  icon: EvtIconInfo = {
    icon: 'clock',
    additionalClasses: 'me-2',
  };

  @Output() layerChange = new EventEmitter<string>();

  getLayerData(data: ChangeLayerData) {
    // eslint-disable-next-line prefer-const
    let layerItems = [];
    data?.layerOrder.forEach((layer) => layerItems.push({ id: layer, value: layer }));
    this.changeLayers = layerItems;
  }

  getLayerColor(layer: string): string {
    const layerColors: string[] = AppConfig.evtSettings.edition.changeSequenceView.layerColors;
    if ((layer !== undefined) && (layerColors[layer.replace('#','')])) {
      return layerColors[layer.replace('#','')];
    }

    return 'black';
  }

  constructor(
    public evtStatusService: EVTStatusService,
  ) {}

  ngOnInit() {
    this.subscription = this.evtStatusService.currentChanges$.pipe(distinctUntilChanged()).subscribe(({ next: (data) => this.getLayerData(data) }));
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

}
