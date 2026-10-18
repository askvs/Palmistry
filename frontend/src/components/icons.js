// Icon set — thin wrapper over lucide-react preserving legacy export names.
// Brand icons stay custom (spec §4.5).
import {
  Activity, ArrowLeft, ArrowRight, ArrowUpDown, Bell, Brain, Calendar, Camera,
  ChartColumn, Check, ChevronDown, CircleCheck, Clock, Compass, Copy, Download,
  Eye, FileText, Hand, Heart, Image as LucideImage, Info, LayoutGrid, Layers,
  List, LogOut, Menu, MessageCircle, Pencil, Play, Plus, Repeat, RotateCcw,
  ScanLine, Search, Send, Settings, Share2, ShieldCheck, SlidersHorizontal,
  Sparkles, Star, Table, Target, Trash2, TrendingUp, TriangleAlert, Upload,
  User, Users, Video, X,
} from "lucide-react";

function wrap(Component, defaultClass = "h-4 w-4", defaultStroke = 1.75) {
  return function Icon({ className = defaultClass, strokeWidth = defaultStroke, ...props }) {
    return (
      <Component className={className} strokeWidth={strokeWidth} aria-hidden="true" {...props} />
    );
  };
}

// Brand ✦ star — filled, hand-drawn, NOT lucide (spec §4.5 exceptions).
export function SparkleIcon({ className = "h-5 w-5" }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M12 2l2.35 7.65L22 12l-7.65 2.35L12 22l-2.35-7.65L2 12l7.65-2.35L12 2z" />
    </svg>
  );
}

// Filled triangle, matching the old PlayIcon silhouette.
export function PlayIcon({ className = "h-4 w-4" }) {
  return <Play className={className} fill="currentColor" aria-hidden="true" />;
}

export const RepeatIcon = wrap(Repeat);
export const HandIcon = wrap(Hand, "h-5 w-5");
export const CardsIcon = wrap(Layers, "h-5 w-5"); // review silhouette in Step 4
export const ScanIcon = wrap(ScanLine, "h-5 w-5");
export const ShieldIcon = wrap(ShieldCheck, "h-5 w-5");
export const ArrowRightIcon = wrap(ArrowRight, "h-4 w-4", 2);
export const ArrowLeftIcon = wrap(ArrowLeft, "h-4 w-4", 2);
export const UploadIcon = wrap(Upload, "h-5 w-5");
export const RetryIcon = wrap(RotateCcw, "h-4 w-4", 2);
export const CheckIcon = wrap(Check, "h-4 w-4", 2.2);
export const MenuIcon = wrap(Menu, "h-5 w-5", 2);
export const CloseIcon = wrap(X, "h-5 w-5", 2);
export const CameraIcon = wrap(Camera, "h-5 w-5");
export const FileTextIcon = wrap(FileText);
export const TableIcon = wrap(Table);
export const TrashIcon = wrap(Trash2);
export const DownloadIcon = wrap(Download);
export const ChartIcon = wrap(ChartColumn); // BarChart3 successor; swap to BarChart3 if this import fails
export const ActivityIcon = wrap(Activity);
export const UserIcon = wrap(User);
export const UsersIcon = wrap(Users);
export const ClockIcon = wrap(Clock);
export const CalendarIcon = wrap(Calendar);
export const CheckCircleIcon = wrap(CircleCheck, "h-5 w-5");
export const AlertIcon = wrap(TriangleAlert, "h-5 w-5");
export const InfoIcon = wrap(Info);
export const SearchIcon = wrap(Search);
export const EyeIcon = wrap(Eye);
export const LogOutIcon = wrap(LogOut);
export const PencilIcon = wrap(Pencil);
export const SendIcon = wrap(Send, "h-4 w-4", 2);
export const ChatIcon = wrap(MessageCircle, "h-5 w-5");
export const TrendingUpIcon = wrap(TrendingUp);
export const CompassIcon = wrap(Compass, "h-5 w-5");
export const LayoutGridIcon = wrap(LayoutGrid);
export const SlidersIcon = wrap(SlidersHorizontal);
export const ArrowUpDownIcon = wrap(ArrowUpDown);
export const ShareIcon = wrap(Share2);
export const PlusIcon = wrap(Plus);
export const SettingsIcon = wrap(Settings);
export const BellIcon = wrap(Bell);
export const SparklesIcon = wrap(Sparkles);
export const VideoIcon = wrap(Video);
export const ImageIcon = wrap(LucideImage, "h-5 w-5");
export const ListIcon = wrap(List);
export const ChevronDownIcon = wrap(ChevronDown, "h-4 w-4", 2);
export const BrainIcon = wrap(Brain);
export const HeartIcon = wrap(Heart);
export const StarIcon = wrap(Star); // call sites control fill via props
export const CopyIcon = wrap(Copy);
export const TargetIcon = wrap(Target);
