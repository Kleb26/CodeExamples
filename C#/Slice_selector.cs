using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using Valve.VR;

public class Slice_selector : MonoBehaviour
{
    public int slice_num;

    private GameObject mode_obj;
    private State mode_void;

    private string obName;
    private int Numb;

    private bool reset;
    public int active_slice;
    public Vector3 stick_out;

    private int last_num;
    private Vector3 offset;

    private bool init;

    // Start is called before the first frame update
    void Start()
    {
        //Offsets for 'hover over' and 'select slice'
        stick_out = new Vector3(0.0f, 1.0f, 0.0f);
        offset = new Vector3(0.0f, 0.2f, 0.0f);

        mode_obj = GameObject.Find("Control_State");

        //Get number of the slice
        GetNumb();

        //Initialize active_slice to be null
        active_slice = 0;
        //Intitialize reset command to be null
        reset = false;
        init = true;
    }

    // Update is called once per frame
    void Update()
    {
        //Get 'mode' from state script.
        mode_void = mode_obj.GetComponent<State>();
        int mode = mode_void.mode;

        //Keep track of previously 'hovered' slice
        last_num = slice_num;
        //Get 'selected'/'hovered' slice number from state script
        slice_num = mode_void.slice_num;
        
        if (mode ==2)
        {
            //If in slice selecting mode is active then slices are offset when 'hovered' over and hence
            //must be lowered when changing mode.
            reset = true;
            //Since actve_slice null is 0 then the 0 slice cannot be selected
            if(Numb != 0)
            {
                //Select a slice to view via right tigger, reset it with it too

                //NOTE: this code does not check the slice number here since the active_slice MUST be set 4all slices and not
                //just on the active slice; otherwise many slices can be active at once and not reset properly.
                if (SteamVR_Input._default.inActions.GrabPinch.GetStateDown(SteamVR_Input_Sources.RightHand))
                {   
                    //Only create an active slice if none exist otherwise lower the slice and reset active_slice
                    if (active_slice == 0)
                    {
                        //Lower the current active slice (unless 0) - legacy code...
                        StickDown();
                        //Set the active slice to the selected one and raise it.
                        active_slice = slice_num;
                        StickUp();
                    }
                    else
                    {
                        StickDown();
                    }
                    
                }

                //Hover fincationality. If selected raise slightly.
                if (Numb == slice_num)
                {
                    //Prevent moving/'hovering' of active slices
                    if(Numb != active_slice)
                    {
                        transform.position = transform.position + offset;
                    }

                }
                if(!init)
                {
                    //Lower again when deselected via last_num functionality
                    if (Numb == last_num)
                    {
                        if (Numb != active_slice)
                        {
                            transform.position = transform.position - offset;
                        }

                    }
                }

                init = false;
            }
        
        }
        else
        {
            //reset by deslected hovering slice (removing offset)
            //note active slices remain.
            if (reset == true)
            {
                if (Numb == slice_num)
                {
                    if (Numb != active_slice)
                    {
                        transform.position = transform.position - offset;
                    }

                }
                reset = false;
                init = true;
            }

        }


    }

    private void StickUp()
    {
        //slice number checked here after active slice chosen to move that individual slice
        if (Numb == active_slice)
        {
            transform.position = transform.position + stick_out;
        }
    }

    private void StickDown()
    {
        if (Numb == active_slice)
        {
            if (Numb != 0)
            {
                transform.position = transform.position - stick_out;
                //correction for if the active slice isn't still selected.
                //An active slice must be selected first hence it is raise by the offset+stick_out
                //If still selected it will return to offset position when made inactive as only removed stick_out
                //If not selected when made inactive the offset will not be removed by acbove code as it will not be last_num either
                //hence it is removed here.
                if(active_slice != last_num)
                {
                    transform.position = transform.position - offset;
                }
            }
            
        }
        //reset the active_slice toensure only one slice can be active at once.
        active_slice = 0;

    }

    private void GetNumb()
    {
        //Get the slice number
        string Name = gameObject.name;

        int start = Name.IndexOf("(") + 1;
        int end = Name.IndexOf(")", start);

        string Numb_str = Name.Substring(start, end - start);
        Numb = int.Parse(Numb_str);
    }
}
