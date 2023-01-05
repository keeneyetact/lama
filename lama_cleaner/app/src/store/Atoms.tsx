import { atom, selector } from 'recoil'
import _ from 'lodash'
import { HDStrategy, LDMSampler } from '../components/Settings/HDSettingBlock'
import { ToastState } from '../components/shared/Toast'

export enum AIModel {
  LAMA = 'lama',
  LDM = 'ldm',
  ZITS = 'zits',
  MAT = 'mat',
  FCF = 'fcf',
  SD15 = 'sd1.5',
  SD2 = 'sd2',
  CV2 = 'cv2',
  Mange = 'manga',
  PAINT_BY_EXAMPLE = 'paint_by_example',
}

export const maskState = atom<File | undefined>({
  key: 'maskState',
  default: undefined,
})

export const paintByExampleImageState = atom<File | undefined>({
  key: 'paintByExampleImageState',
  default: undefined,
})

export interface Rect {
  x: number
  y: number
  width: number
  height: number
}

interface AppState {
  file: File | undefined
  disableShortCuts: boolean
  isInpainting: boolean
  isDisableModelSwitch: boolean
  isInteractiveSeg: boolean
  isInteractiveSegRunning: boolean
  interactiveSegClicks: number[][]
  showFileManager: boolean
}

export const appState = atom<AppState>({
  key: 'appState',
  default: {
    file: undefined,
    disableShortCuts: false,
    isInpainting: false,
    isDisableModelSwitch: false,
    isInteractiveSeg: false,
    isInteractiveSegRunning: false,
    interactiveSegClicks: [],
    showFileManager: false,
  },
})

export const propmtState = atom<string>({
  key: 'promptState',
  default: '',
})

export const negativePropmtState = atom<string>({
  key: 'negativePromptState',
  default: '',
})

export const isInpaintingState = selector({
  key: 'isInpainting',
  get: ({ get }) => {
    const app = get(appState)
    return app.isInpainting
  },
  set: ({ get, set }, newValue: any) => {
    const app = get(appState)
    set(appState, { ...app, isInpainting: newValue })
  },
})

export const showFileManagerState = selector({
  key: 'showFileManager',
  get: ({ get }) => {
    const app = get(appState)
    return app.showFileManager
  },
  set: ({ get, set }, newValue: any) => {
    const app = get(appState)
    set(appState, { ...app, showFileManager: newValue })
  },
})

export const fileState = selector({
  key: 'fileState',
  get: ({ get }) => {
    const app = get(appState)
    return app.file
  },
  set: ({ get, set }, newValue: any) => {
    const app = get(appState)
    set(appState, {
      ...app,
      file: newValue,
      interactiveSegClicks: [],
      isInteractiveSeg: false,
      isInteractiveSegRunning: false,
    })
  },
})

export const isInteractiveSegState = selector({
  key: 'isInteractiveSegState',
  get: ({ get }) => {
    const app = get(appState)
    return app.isInteractiveSeg
  },
  set: ({ get, set }, newValue: any) => {
    const app = get(appState)
    set(appState, { ...app, isInteractiveSeg: newValue })
  },
})

export const isInteractiveSegRunningState = selector({
  key: 'isInteractiveSegRunningState',
  get: ({ get }) => {
    const app = get(appState)
    return app.isInteractiveSegRunning
  },
  set: ({ get, set }, newValue: any) => {
    const app = get(appState)
    set(appState, { ...app, isInteractiveSegRunning: newValue })
  },
})

export const interactiveSegClicksState = selector({
  key: 'interactiveSegClicksState',
  get: ({ get }) => {
    const app = get(appState)
    return app.interactiveSegClicks
  },
  set: ({ get, set }, newValue: any) => {
    const app = get(appState)
    set(appState, { ...app, interactiveSegClicks: newValue })
  },
})

export const isDisableModelSwitchState = selector({
  key: 'isDisableModelSwitchState',
  get: ({ get }) => {
    const app = get(appState)
    return app.isDisableModelSwitch
  },
  set: ({ get, set }, newValue: any) => {
    const app = get(appState)
    set(appState, { ...app, isDisableModelSwitch: newValue })
  },
})

export const croperState = atom<Rect>({
  key: 'croperState',
  default: {
    x: 0,
    y: 0,
    width: 512,
    height: 512,
  },
})

export const croperX = selector({
  key: 'croperX',
  get: ({ get }) => get(croperState).x,
  set: ({ get, set }, newValue: any) => {
    const rect = get(croperState)
    set(croperState, { ...rect, x: newValue })
  },
})

export const croperY = selector({
  key: 'croperY',
  get: ({ get }) => get(croperState).y,
  set: ({ get, set }, newValue: any) => {
    const rect = get(croperState)
    set(croperState, { ...rect, y: newValue })
  },
})

export const croperHeight = selector({
  key: 'croperHeight',
  get: ({ get }) => get(croperState).height,
  set: ({ get, set }, newValue: any) => {
    const rect = get(croperState)
    set(croperState, { ...rect, height: newValue })
  },
})

export const croperWidth = selector({
  key: 'croperWidth',
  get: ({ get }) => get(croperState).width,
  set: ({ get, set }, newValue: any) => {
    const rect = get(croperState)
    set(croperState, { ...rect, width: newValue })
  },
})

interface ToastAtomState {
  open: boolean
  desc: string
  state: ToastState
  duration: number
}

export const toastState = atom<ToastAtomState>({
  key: 'toastState',
  default: {
    open: false,
    desc: '',
    state: 'default',
    duration: 3000,
  },
})

export const shortcutsState = atom<boolean>({
  key: 'shortcutsState',
  default: false,
})

export interface HDSettings {
  hdStrategy: HDStrategy
  hdStrategyResizeLimit: number
  hdStrategyCropTrigerSize: number
  hdStrategyCropMargin: number
  enabled: boolean
}

type ModelsHDSettings = { [key in AIModel]: HDSettings }

export enum CV2Flag {
  INPAINT_NS = 'INPAINT_NS',
  INPAINT_TELEA = 'INPAINT_TELEA',
}

export interface Settings {
  show: boolean
  showCroper: boolean
  downloadMask: boolean
  graduallyInpainting: boolean
  runInpaintingManually: boolean
  model: AIModel
  hdSettings: ModelsHDSettings

  // For LDM
  ldmSteps: number
  ldmSampler: LDMSampler

  // For ZITS
  zitsWireframe: boolean

  // For SD
  sdMaskBlur: number
  sdMode: SDMode
  sdStrength: number
  sdSteps: number
  sdGuidanceScale: number
  sdSampler: SDSampler
  sdSeed: number
  sdSeedFixed: boolean // true: use sdSeed, false: random generate seed on backend
  sdNumSamples: number
  sdMatchHistograms: boolean

  // For OpenCV2
  cv2Radius: number
  cv2Flag: CV2Flag

  // Paint by Example
  paintByExampleSteps: number
  paintByExampleGuidanceScale: number
  paintByExampleSeed: number
  paintByExampleSeedFixed: boolean
  paintByExampleMaskBlur: number
  paintByExampleMatchHistograms: boolean
}

const defaultHDSettings: ModelsHDSettings = {
  [AIModel.LAMA]: {
    hdStrategy: HDStrategy.CROP,
    hdStrategyResizeLimit: 2048,
    hdStrategyCropTrigerSize: 1280,
    hdStrategyCropMargin: 196,
    enabled: true,
  },
  [AIModel.LDM]: {
    hdStrategy: HDStrategy.CROP,
    hdStrategyResizeLimit: 1080,
    hdStrategyCropTrigerSize: 1080,
    hdStrategyCropMargin: 128,
    enabled: true,
  },
  [AIModel.ZITS]: {
    hdStrategy: HDStrategy.CROP,
    hdStrategyResizeLimit: 1024,
    hdStrategyCropTrigerSize: 1024,
    hdStrategyCropMargin: 128,
    enabled: true,
  },
  [AIModel.MAT]: {
    hdStrategy: HDStrategy.CROP,
    hdStrategyResizeLimit: 1024,
    hdStrategyCropTrigerSize: 512,
    hdStrategyCropMargin: 128,
    enabled: true,
  },
  [AIModel.FCF]: {
    hdStrategy: HDStrategy.CROP,
    hdStrategyResizeLimit: 512,
    hdStrategyCropTrigerSize: 512,
    hdStrategyCropMargin: 128,
    enabled: false,
  },
  [AIModel.SD15]: {
    hdStrategy: HDStrategy.ORIGINAL,
    hdStrategyResizeLimit: 768,
    hdStrategyCropTrigerSize: 512,
    hdStrategyCropMargin: 128,
    enabled: false,
  },
  [AIModel.SD2]: {
    hdStrategy: HDStrategy.ORIGINAL,
    hdStrategyResizeLimit: 768,
    hdStrategyCropTrigerSize: 512,
    hdStrategyCropMargin: 128,
    enabled: false,
  },
  [AIModel.PAINT_BY_EXAMPLE]: {
    hdStrategy: HDStrategy.ORIGINAL,
    hdStrategyResizeLimit: 768,
    hdStrategyCropTrigerSize: 512,
    hdStrategyCropMargin: 128,
    enabled: false,
  },
  [AIModel.Mange]: {
    hdStrategy: HDStrategy.CROP,
    hdStrategyResizeLimit: 1280,
    hdStrategyCropTrigerSize: 1024,
    hdStrategyCropMargin: 196,
    enabled: true,
  },
  [AIModel.CV2]: {
    hdStrategy: HDStrategy.RESIZE,
    hdStrategyResizeLimit: 1080,
    hdStrategyCropTrigerSize: 512,
    hdStrategyCropMargin: 128,
    enabled: true,
  },
}

export enum SDSampler {
  ddim = 'ddim',
  pndm = 'pndm',
  klms = 'k_lms',
  kEuler = 'k_euler',
  kEulerA = 'k_euler_a',
  dpmPlusPlus = 'dpm++',
}

export enum SDMode {
  text2img = 'text2img',
  img2img = 'img2img',
  inpainting = 'inpainting',
}

export const settingStateDefault: Settings = {
  show: false,
  showCroper: false,
  downloadMask: false,
  graduallyInpainting: true,
  runInpaintingManually: false,
  model: AIModel.LAMA,
  hdSettings: defaultHDSettings,

  ldmSteps: 25,
  ldmSampler: LDMSampler.plms,

  zitsWireframe: true,

  // SD
  sdMaskBlur: 5,
  sdMode: SDMode.inpainting,
  sdStrength: 0.75,
  sdSteps: 50,
  sdGuidanceScale: 7.5,
  sdSampler: SDSampler.pndm,
  sdSeed: 42,
  sdSeedFixed: true,
  sdNumSamples: 1,
  sdMatchHistograms: false,

  // CV2
  cv2Radius: 5,
  cv2Flag: CV2Flag.INPAINT_NS,

  // Paint by Example
  paintByExampleSteps: 50,
  paintByExampleGuidanceScale: 7.5,
  paintByExampleSeed: 42,
  paintByExampleMaskBlur: 5,
  paintByExampleSeedFixed: false,
  paintByExampleMatchHistograms: false,
}

const localStorageEffect =
  (key: string) =>
  ({ setSelf, onSet }: any) => {
    const savedValue = localStorage.getItem(key)
    if (savedValue != null) {
      const storageSettings = JSON.parse(savedValue)
      storageSettings.show = false

      const restored = _.merge(
        _.cloneDeep(settingStateDefault),
        storageSettings
      )
      setSelf(restored)
    }

    onSet((newValue: Settings, val: string, isReset: boolean) =>
      isReset
        ? localStorage.removeItem(key)
        : localStorage.setItem(key, JSON.stringify(newValue))
    )
  }

const ROOT_STATE_KEY = 'settingsState4'
// Each atom can reference an array of these atom effect functions which are called in priority order when the atom is initialized
// https://recoiljs.org/docs/guides/atom-effects/#local-storage-persistence
export const settingState = atom<Settings>({
  key: ROOT_STATE_KEY,
  default: settingStateDefault,
  effects: [localStorageEffect(ROOT_STATE_KEY)],
})

export const seedState = selector({
  key: 'seed',
  get: ({ get }) => {
    const settings = get(settingState)
    switch (settings.model) {
      case AIModel.PAINT_BY_EXAMPLE:
        return settings.paintByExampleSeedFixed
          ? settings.paintByExampleSeed
          : -1
      default:
        return settings.sdSeedFixed ? settings.sdSeed : -1
    }
  },
  set: ({ get, set }, newValue: any) => {
    const settings = get(settingState)
    switch (settings.model) {
      case AIModel.PAINT_BY_EXAMPLE:
        if (!settings.paintByExampleSeedFixed) {
          set(settingState, { ...settings, paintByExampleSeed: newValue })
        }
        break
      default:
        if (!settings.sdSeedFixed) {
          set(settingState, { ...settings, sdSeed: newValue })
        }
    }
  },
})

export const hdSettingsState = selector({
  key: 'hdSettings',
  get: ({ get }) => {
    const settings = get(settingState)
    return settings.hdSettings[settings.model]
  },
  set: ({ get, set }, newValue: any) => {
    const settings = get(settingState)
    const hdSettings = settings.hdSettings[settings.model]
    const newHDSettings = { ...hdSettings, ...newValue }

    set(settingState, {
      ...settings,
      hdSettings: { ...settings.hdSettings, [settings.model]: newHDSettings },
    })
  },
})

export const isSDState = selector({
  key: 'isSD',
  get: ({ get }) => {
    const settings = get(settingState)
    return settings.model === AIModel.SD15 || settings.model === AIModel.SD2
  },
})

export const isPaintByExampleState = selector({
  key: 'isPaintByExampleState',
  get: ({ get }) => {
    const settings = get(settingState)
    return settings.model === AIModel.PAINT_BY_EXAMPLE
  },
})

export const runManuallyState = selector({
  key: 'runManuallyState',
  get: ({ get }) => {
    const settings = get(settingState)
    const isSD = get(isSDState)
    const isPaintByExample = get(isPaintByExampleState)
    return settings.runInpaintingManually || isSD || isPaintByExample
  },
})
